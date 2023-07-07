from odoo import api, fields, models
from PyPDF2 import PdfFileWriter, PdfFileReader
from odoo.exceptions import UserError
from asyncio.log import logger
import io
import codecs

class WayfairLabels(models.Model):
    _name = 'wayfair.labels'
    _inherit = 'mail.thread'
    _description = 'Wayfair Labels'

    name = fields.Char(string='Name')
    label = fields.Binary(string='Label')
    shop_id = fields.Many2one("wayfair.seller","Wayfair Shop")
    mapped_sale_orer_ids = fields.One2many("sale.order","label_id","Mapped Sale Orders",compute="_compute_mapped_sale_orders")
    orders_mapped = fields.Boolean("Orders Mapped")

    @api.model
    def create(self, values):
        # Add code here
        result =  super(WayfairLabels, self).create(values)
        for res in result:
            res.shop_id = self.env.context.get('active_id')
        return result
    
    

    def split_and_map_labels(self):
        # import base64
        # import PyPDF2
        # attachments = self.env['ir.attachment'].search([('res_model','=','wayfair.labels'),('res_id','=',self.id)])
        # order_list = []
        # for attachment in attachments:
        # decode the base64 encoded pdf content
        #     pdf_content = base64.b64decode(attachment.datas)
        #     file_result = open("test.pdf",'wb')
        #     file_result.write(pdf_content)

        #     from pdfreader import SimplePDFViewer
        #     orders_mapped = 0
        #     viewer = SimplePDFViewer(pdf_content)
        #     all_pages = [p for p in viewer.doc.pages()]
        #     number_of_pages = len(all_pages)
        #     for page_number in range(1, number_of_pages + 1):
        #         viewer.navigate(int(page_number))
        #         viewer.render()
        #         page_strings = " ".join(viewer.canvas.strings).replace('     ', '\n\n').strip()
        #         print(f'Current Page Number: {page_number}')
        #         print(f'Page Text: {page_strings}')
        #         page_strings = page_strings.split(" ")
        #         # import pdb;pdb.set_trace()
        #         order_number = sku = None
        #         if self.shop_id.warehouse_id.code == 'IFUL':
        #             ref_index = page_strings.index("Ref:")
        #             order_number = page_strings[ref_index + 2]
        #             if order_number not in order_list:
        #                 order_list.append(order_number)
        #             else:
        #                 logger.info("Order %s already mapped with other sku also", order_number)
        #             sku = page_strings[ref_index + 6]
        #         else:
        #             for str in page_strings:
        #                 if str.startswith("UK"):
        #                     order_number = str

                # order = self.map_sale_order(order_number,attachment,sku)
                # logger.info(order_list)
                # if order:
                    # orders_mapped += 1
                    # order.write({'label_id': self.id})
                # if orders_mapped > 0:
                    # self.write({'orders_mapped':True})
                pass
                

    def map_sale_order(self,orderNumber,attachment,sku):
        sale_order = self.env['sale.order'].search([('wayfair_order_id','=',orderNumber)],limit=1)
        if sale_order:
            attachments = self.env['ir.attachment'].search([('res_model','=','sale.order'),('res_id','=', sale_order.id)])
            #Remove Alrady exist attachments
            attach = self.env['ir.attachment'].create({'name': sku,'res_model': 'sale.order', 'res_id': sale_order.id, 'datas': attachment.datas})

            if attach:
                print("Sale Orders Mapped %s", sale_order)
                return sale_order
            else:
                return False
        else:
            print("Order Not found to map")

    
    @api.depends("orders_mapped")
    def _compute_mapped_sale_orders(self):
        for rec in self:
            if self.message_attachment_count > 0 and self.orders_mapped:
                orders = self.env['sale.order'].search([('label_id','=',rec.id)])
                if len(orders):
                    for order in orders:
                        rec.mapped_sale_orer_ids =  rec.mapped_sale_orer_ids + order
                else:
                    rec.mapped_sale_orer_ids = None
            else:
                rec.mapped_sale_orer_ids = None
                
    
    def reset_and_map(self):
        for res in self:
            for order in res.mapped_sale_orer_ids:
                #Remove Alrady exist attachments
                attachments = self.env['ir.attachment'].search([('res_model','=','sale.order'),('res_id','=', order.id)])
                if len(attachments):
                    for attach in attachments:
                        attach.unlink()
            res.write({'orders_mapped': False})
