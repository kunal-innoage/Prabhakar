from odoo import fields , models
import logging
_logger = logging.getLogger(__name__)

class SaleReport(models.Model):
    _inherit = 'sale.report'
    

    total_cogs = fields.Float("Total COGS")
    
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['total_cogs'] = ",l.total_cogs"
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
    

    def _group_by_sale(self, groupby=''):
        groupby_ = """
            l.product_id,
            l.order_id,
            l.total_cogs, 
            t.uom_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.partner_id,
            s.user_id,
            s.state,
            s.company_id,
            s.campaign_id,
            s.medium_id,
            s.source_id,
            s.pricelist_id,
            s.analytic_account_id,
            s.team_id,
            p.product_tmpl_id,
            partner.country_id,
            partner.industry_id,
            partner.commercial_partner_id,
            l.discount,

            s.id %s
        """ % (groupby)
        return groupby_

 

