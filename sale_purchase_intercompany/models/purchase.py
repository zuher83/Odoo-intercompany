# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('partner_id', 'company_id')
    def _intercompany_compute(self):
        for o in self:
            company = self.env['res.company'].search([('partner_id', '=', o.partner_id.id)])
            if company:
                if o.partner_id.id == company[0].partner_id.id:
                    o.intercompany = True
            else:
                o.intercompany = False


    intercompany = fields.Boolean(string="Intercompany", compute="_intercompany_compute", copy=False)
    auto_generate_sale = fields.Boolean(string="Auto generated sale", readonly=True, default=False, copy=False)
    auto_sale_id = fields.Many2one('sale.order', string='Auto Sale Order', readonly=True, copy=False, _prefetch=False)

    @api.multi
    def launch_intercompany_sale(self):
        for o in self:
            ctx = {
                'default_type': 'purchase',
                'default_company_id': o.company_id.id
            }

            return {
                'name': _('Create Sale order'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.purchase.intercompany.wizard',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'domain': [],
                'target': 'new',
            }
