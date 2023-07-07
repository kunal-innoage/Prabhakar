from odoo import fields,api,models

class CDiscountStock(models.Model):
    _name = 'cdiscount.stock'
    _description = 'CDiscount Stock Managment'


    name = fields.Char("Product Name")
    brand_name  = fields.Char("Brand")
    bar_code = fields.Char("Ean")
    isbn = fields.Char("ISBN")
    product_type = fields.Char("Product Type")
    odoo_product_id = fields.Many2one('product.template','Product')
    sku = fields.Char("SKU")
    on_shop_qty = fields.Char("Stock")
    ref = fields.Char("Your reference")
    price = fields.Float("All taxes included price)")
    vat = fields.Float("VAT (%)")
    on_hand_qty = fields.Char("On Hand Quantity")
    discount = fields.Float("Discount (%)")
    condition = fields.Char("Product Under Condition")
    eco_part_amount = fields.Char("Eco Part (amount)")
    aed_amount_france = fields.Char("aed (amount) (france)")
    private_cpy_amount = fields.Char("Private Copying (amount)")
    chemical_amount = fields.Char("Chemical Tax (amount)")
    low_price_allowed = fields.Char("Lowest price allowed (€)(TTC)")
    prep_time = fields.Char("Preparation time(nb working days max)")
    additional_facultive = fields.Char("Additional Facultative")
    principal = fields.Char("Principal")
    additional_facultatif = fields.Char("Additionnel Facultatif")
    offer_status = fields.Selection([
        ('active','Active'),
        ('inactive','InActive')
    ])
    stock_type = fields.Selection([
        ('fullfill','Fulfillment Stock'),
        ('makretplace','Marketplace')
    ])

    @api.model_create_multi
    def create(self, vals):
        result = super(CDiscountStock, self).create(vals)
        for res in result:
            mapped_product = self.env['product.template'].search([('default_code','=', res.ref)])
            if mapped_product:
                res.odoo_product_id = mapped_product.id
                res.name = mapped_product.name
                res.on_hand_qty = mapped_product.qty_available
        return result