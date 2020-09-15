# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_id = fields.Many2one(index=True)
    is_stock_valuation = fields.Boolean(
        'Is Stock Valuation',
        compute="_compute_is_stock_valuation")

    def _compute_is_stock_valuation(self):
        for rec in self:
            if not rec.product_id:
                rec.is_stock_valuation = False
            rec.is_stock_valuation = (rec.account_id ==
                rec.product_id.categ_id.property_stock_valuation_account_id)

    def write(self, vals):
        if vals.get('product_id', False):
            product = vals.get('product_id')
            product = self.env['product.product'].browse(product)
        else:
            product = self.product_id
        if vals.get('account_id', False):
            account_id = vals.get('account_id')
            account = self.env['account.account'].browse(account_id)
        else:
            account = self.account_id

        # delete existing revaluation
        for rec in self:
            self.env['stock.valuation.layer'].sudo().search(
                [('account_move_line_id', '=', rec.id)]).unlink()

        for rec in self:
            if not rec.is_stock_valuation:
                continue
            account_value = sum(
                rec.filtered(
                    lambda aml: aml.account_id == account).mapped('debit')) - sum(
                rec.filtered(
                    lambda aml: aml.account_id == account).mapped('credit'))
            account_qty = rec.quantity
            layer = self.env['stock.valuation.layer'].create({
                'value': 0,
                'unit_cost': 0,
                'quantity': 0,
                'remaining_qty': 0,
                'account_move_line_id': rec.id,
                'account_move_id': rec.move_id.id,
                'account_value': account_value,
                'account_qty_at_date': account_qty,
                'description': 'Inventory valuation',
                'product_id': product.id,
                'company_id': rec.company_id.id,
            })
        return super(AccountMoveLine, self).write(vals)
