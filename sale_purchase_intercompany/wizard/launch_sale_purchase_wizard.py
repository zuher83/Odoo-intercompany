# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SalePourchaseWizard(models.Model):
    _name = 'sale.purchase.intercompany.wizard'
    _description = 'Sale and purchase intercompany wizard'

    type = fields.Selection(string="", selection=[('sale', 'Sale'), ('purchase', 'Purchase'), ],
                            required=True, )
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                         'sale.purchase.intercompany.wizard'))
    inter_company_id = fields.Many2one('res.company', string='Company')
    partner_id = fields.Many2one('res.partner', string='Partner')
    operation_type = fields.Selection(string="Operation type", selection=[('internal', 'Internal'),
                                                                          ('External', 'External'),
                                                                          ], required=True,
                                      default='internal')
    add_margin = fields.Boolean(string="Add Margin",  )
    margin_percent = fields.Float(string="Margin Percent",  required=False, )
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')


    @api.multi
    def launchprocess(self):
        for s in self:
            if s.type == 'sale':
                s.sudo().launch_from_sale_process(order=self._context.get('active_id', []))
            if s.type == 'purchase':
                so = s.launch_from_purchase_process(order=self._context.get('active_id', []))
                return self.action_view_sale(so)

    @api.multi
    def launch_from_sale_process(self, order):
        for o in self.env['sale.order'].browse(order):

            if o.auto_generate_purchase is True:
                raise ValidationError(
                        _('This order has already been processed!'))

            purchase_data = {
                'date_order': o.date_order,
                'partner_ref': o.name,
                'partner_id': self.company_id.partner_id.id,
                'date_planned': o.commitment_date,
                'company_id': self.inter_company_id.id,
                'auto_sale_id': o.id,
                'create_uid': self._uid
                }
            po = self.env['purchase.order'].sudo(self.env.user.id).with_context(
                    force_company=self.inter_company_id.id, uid=self._uid).create(
                    purchase_data)

            for l in o.order_line:
                line = self._prepare_purchase_line_data(po, l)
                self.env['purchase.order.line'].with_context(
                        force_company=self.inter_company_id.id).create(line)

            warehouse = self.env['stock.picking.type'].with_context(
                    force_company=self.inter_company_id.id).search([('code', '=', 'incoming'),
                                                                    ('warehouse_id.company_id', '=',
                                                                     self.inter_company_id.id)])
            po.write({'picking_type_id': warehouse.id})
            body = (_('This order are generated automatically from %s company') %
                    self.company_id.name)
            po.sudo(self.env.user.id).message_post(body)
            o.write({'auto_generate_purchase': True, 'auto_purchase_id': po.id})

        return {'type': 'ir.actions.act_window_close'}

    def _prepare_sale_line_data(self, so, line):
        taxes = line.product_id.taxes_id
        fpos = so.fiscal_position_id
        taxes_id = fpos.map_tax(taxes) if fpos else taxes

        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == self.company_id.id)

        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'product_uom_qty': line.product_qty,
            'product_uom': line.product_uom.id,
            'price_unit': line.price_unit,
            'tax_id': [(6, 0, taxes_id.ids)],
            'order_id': so.id,
            }

    def _prepare_purchase_line_data(self, po, line):
        taxes = line.sudo().with_context(
                force_company=self.inter_company_id.id).product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes) if fpos else taxes

        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == self.inter_company_id.id)

        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'price_unit': line.price_unit,
            'date_planned': line.order_id.commitment_date,
            'taxes_id': [(6, 0, taxes_id.ids)],
            'order_id': po.id,
            }

    @api.multi
    def launch_from_purchase_process(self, order):
        for o in self.env['purchase.order'].browse(order):

            if o.auto_generate_sale is True:
                raise ValidationError(
                        _('This order has already been processed!'))

            sale_data = {
                'date_order': o.date_order,
                'client_order_ref': o.name,
                'warehouse_id': self.warehouse_id.id,
                'auto_purchase_id': o.id

                }
            if self.operation_type == 'internal':
                sale_data['partner_id'] = self.inter_company_id.partner_id.id,
            if self.operation_type == 'external':
                sale_data['partner_id'] = self.partner_id.id,

            so = self.env['sale.order'].create(
                    sale_data)

            for l in o.order_line:
                line = self._prepare_sale_line_data(so, l)
                if self.add_margin is True and self.margin_percent > 0.0:
                    cur_price = line['price_unit']*(1+self.margin_percent/100)
                    line['price_unit'] = cur_price

                so_lines = self.env['sale.order.line'].create(line)
                if self.add_margin is not True:
                    so_lines.update_pricelist_lines_new_prices()

            o.write({'auto_generate_sale': True, 'auto_sale_id': so.id})

        return so.id

    @api.multi
    def action_view_sale(self, sale):
        self.ensure_one()
        res = self.env.ref('sale.view_order_form')

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'view_id': res.id,
            'type': 'ir.actions.act_window',
            'res_id': sale,
        }
