# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'


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
    auto_generate_purchase = fields.Boolean(string="Auto generated purchase", readonly=True, default=False, copy=False)
    auto_purchase_id = fields.Many2one('purchase.order',
                                      string='Auto Purchase Order',
                                      readonly=True, copy=False,
                                      _prefetch=False)

    @api.multi
    def launch_intercompany_purchase(self):
        for o in self:
            if o.intercompany is True:
                purchase_company = self.env['res.company'].search([('partner_id', '=', o.partner_id.id)])
                ctx = {
                    'default_inter_company_id': purchase_company[0].id,
                    'default_type': 'sale',
                    'default_company_id': o.company_id.id
                }

            return {
                'name': _('Create Purchase order'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.purchase.intercompany.wizard',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': ctx,
                'domain': [],
                'target': 'new',
            }
