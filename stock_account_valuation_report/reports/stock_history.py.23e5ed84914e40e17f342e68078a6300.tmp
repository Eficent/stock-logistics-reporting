# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
#   (<https://www.eficent.com>)
# Copyright 2018 Aleph Objects, Inc.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class StockHistory(models.Model):
    _inherit = 'stock.history'
    valuation = fields.Char(related='product_id.valuation')
    account_qty_at_date = fields.Float(
        'Accounting Quantity', compute='_compute_inventory_acc_value')
    account_value = fields.Float(
        'Accounting Value', compute='_compute_inventory_acc_value')
    stock_fifo_real_time_aml_ids = fields.Many2many(
        'account.move.line', compute='_compute_inventory_acc_value')

    def _compute_inventory_acc_value(self):
        stock_move = self.env['stock.move']
        self.env['account.move.line'].check_access_rights('read')
        to_date = self.env.context.get('date', False)
        accounting_values = {}
        query = """
            SELECT aml.product_id, aml.account_id,
            sum(aml.debit) - sum(aml.credit), sum(quantity),
            array_agg(aml.id)
            FROM account_move_line AS aml
            WHERE aml.product_id IN %%s
            AND aml.company_id=%%s %s
            GROUP BY aml.product_id, aml.account_id"""
        params = (tuple(self._ids, ), self.env.user.company_id.id)
        if to_date:
            # pylint: disable=sql-injection
            query = query % ('AND aml.date <= %s',)
            params = params + (to_date,)
        else:
            query = query % ('',)
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        for row in res:
            accounting_values[(row[0], row[1])] = (row[2], row[3],
                                                    list(row[4]))

        products_with_value = self.env['product.product'].search([('valuation', '=', 'real_time')])
        for rec in self:
            product = rec.product_id
            # Retrieve the values from accounting
            if product.valuation == 'real_time':
                valuation_account_id = \
                    product.categ_id.property_stock_valuation_account_id.id
                value, quantity, aml_ids = accounting_values.get(
                    (product.id, valuation_account_id)) or (0, 0, [])
                rec.account_value = value
                rec.account_qty_at_date = quantity
                rec.stock_fifo_real_time_aml_ids = \
                    self.env['account.move.line'].browse(aml_ids)

    def action_view_amls(self):
        self.ensure_one()
        to_date = self.env.context.get('date')
        tree_view_ref = self.env.ref('account.view_move_line_tree')
        form_view_ref = self.env.ref('account.view_move_line_form')
        action = {'name': _('Accounting Valuation at date'),
                  'type': 'ir.actions.act_window', 'view_type': 'form',
                  'view_mode': 'tree,form', 'context': self.env.context,
                  'res_model': 'account.move.line',
                  'domain': [('id', 'in', self.with_context(
                      to_date=to_date).stock_fifo_real_time_aml_ids.ids)],
                  'views': [(tree_view_ref.id, 'tree'),
                            (form_view_ref.id, 'form')]}
        return action
