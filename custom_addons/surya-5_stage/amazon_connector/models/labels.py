from odoo import models,fields,api
import os,glob
from asyncio.log import logger
from odoo.exceptions import UserError
import base64


class AmazonLabels(models.Model):
    _name = 'amazon.labels'
    _description = 'Amazon.labels'
    _inherit = 'mail.thread'

    label = fields.Binary(string='Label')
    name = fields.Char(string='Name')
    order_id = fields.Char("Amazon Order ID")
    sale_order = fields.Many2one("sale.order","Sale Order")
    amazon_shop_id = fields.Many2one(comodel_name='amazon.seller', string='Amazon Shop')
    split_label_ids = fields.One2many(comodel_name='split.labels', inverse_name='label_id', string='Labels')
    splitting_done = fields.Boolean("Split Operation Done")
    
    
    @api.model_create_multi
    def create(self,vals):
        
        result = super(AmazonLabels,self).create(vals)
        for res in result:
            res.amazon_shop_id = res._context.get('active_id')
        return result

    def split_and_map_labels(self):
        if not self.splitting_done:
            # if not os.path.exists(os.getcwd()+'/labels'):
            #     os.makedirs("labels")
            # from PyPDF2 import PdfFileWriter, PdfFileReader
            # import base64

            # decoded = None
            # with open('Output.pdf', 'wb') as output_file:
            #     decoded = base64.b64decode(self.label)
            #     output_file.write(decoded)

            # inputpdf = PdfFileReader(open("Output.pdf", "rb"))

            # for i in range(inputpdf.numPages):
            #     output = PdfFileWriter()
            #     page = inputpdf.getPage(i)
            #     page.rotateClockwise(90)
            #     output.addPage(page)
            #     with open("labels/label%s.pdf" % str(i + 1), "wb") as outputStream:
            #         output.write(outputStream)

            
            # os.chdir(os.getcwd() + '/labels')
            # print(os.getcwd())
            # pdfs = []
            # for file in glob.glob("*.pdf"):
            #     print(file)
            #     pdfs.append(file)

            label_count = 0 
            # for pdf in pdfs:
            #     with open(pdf, "rb") as f:
            #         encoded = base64.b64encode(f.read())
            #         split_label_rec = self.env['split.labels'].create({
            #             'label': encoded,
            #             'name': pdf,
            #             'label_id': self.id
            #         })
            #         if split_label_rec:
            #             label_count += 1
            #             print("label record created with ID %s ", str(split_label_rec.id))
            attachments = self.env['ir.attachment'].search([('res_model','=','amazon.labels'),('res_id','=',self.id)])
            for attachment in attachments:
                split_label_rec = self.env['split.labels'].create({
                        'label': attachment.datas,
                        'name': 'label',
                        'label_id': self.id
                    })
                if split_label_rec:
                    label_count += 1
                    base64_file = base64.b64encode(attachment.datas)
                    print("label record created with ID %s ", str(split_label_rec.id))
                    attach = self.env['ir.attachment'].create({'name': 'label','res_model': 'split.labels', 'res_id': split_label_rec.id, 'datas': attachment.datas})
                    if attach:
                        logger.info("Attachments are created in ")

            if label_count > 0:
                self.write({'splitting_done': True})
                return {
                    'name': ('Labels'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'split.labels',
                    'view_mode': 'tree,form',
                    'target': 'current',
                    'domain': [('label_id','=',self.id)],
                    'context': {'order':'name'},
                }
        else:
            raise UserError("Split operation already done. Click on Reset and map to do it again")

    def action_view_split_labels(self):
        return {
            'name': ('Labels'),
            'type': 'ir.actions.act_window',
            'res_model': 'split.labels',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('label_id','=',self.id)],
            'context': {'order':'name'},
        }
    
    
    def reset_and_split(self):
        labels = self.env['split.labels'].search([("label_id","=",self.id)])
        for label in labels:
            label.unlink()
        self.write({'splitting_done': False})

class SplitLabels(models.Model):
    _name = 'split.labels'
    _description = 'Split Labels'
    _inherit = "mail.thread"


    label = fields.Binary(string='Label')
    name = fields.Char(string='Name')
    order_id = fields.Char("Amazon Order ID")
    sale_order = fields.Many2one("sale.order","Sale Order")
    label_id = fields.Many2one('amazon.labels','Label ID')

    #Map Sale Order to Labels based on amazon order ID entered by user
    def map_sale_orders(self):
        for res in self:
            if res.order_id:
                so = self.env['sale.order'].search([('amazon_order_id','=',res.order_id)], limit=1)
                if res.label and so:
                    res.sale_order = so.id
                    attachments = self.env['ir.attachment'].search([('res_model','=','split.labels'),('res_id','=',self.id)])
                    for attachment in attachments:
                        self.attach_label_to_order(so, attachment)
    
    def attach_label_to_order(self,order,attachment):
        attach = self.env['ir.attachment'].create({'name': 'label','res_model': 'sale.order', 'res_id': order.id, 'datas': attachment.datas})
        if attach:
            logger.info("Label attached to %s ", order.name)
        
    
