from odoo import models, fields,api, _
import logging 
_logger = logging.getLogger(__name__)


class ProductAttribute(models.Model):
    _name = 'product.attribute.custom'
    _description = 'Product Custom Attributes'
    _rec_name = "sku"

    sku = fields.Char(string='SKU')
    color = fields.Char(string='Color')
    style = fields.Char("Style")
    material = fields.Char("Material")
    size = fields.Char("Size")
    backing_material = fields.Char("Backing Material")
    shape = fields.Char("Shape")
    care_instructions = fields.Char("Care Instructions")



    product_id = fields.Many2one('product.template', string='Product')



    def add_custom_value(self, attribute_id, value_name):       
        try:
            value_id = self.env["product.attribute.value"].create({
                "name": value_name,
                "attribute_id": attribute_id.id,
            })
            _logger.info(" %r  - Product Attribute Value Created ", value_id )
            return value_id
        except Exception as e:
            _logger.info("Error while adding new value inside %r and error - %r", attribute_id, e)
            return False

    def map_product_attributes(self):
        
        try:
            for prod in self:
                product_id = self.env["product.template"].search([('default_code', '=', prod.sku)], limit=1)
                if product_id:
                    prod.product_id = product_id
                    attribute_line_ids = []
                    product_attribute = self.env["product.attribute"]
                    product_attr_data = {}
                    for line in  product_id.attribute_line_ids:
                        value_list = []
                        for value in line.value_ids:
                            value_list += [value]
                        product_attr_data[line.attribute_id.id] = value_list
                    product_attributes = [line.attribute_id for line in product_id.attribute_line_ids]
                    
                    ###################
                    # STYLE ATTRIBUTE #
                    ###################
                                        
                    if prod.style:
                        attribute_id = product_attribute.search([("name", "=", "Style")], limit=1)
                        if attribute_id:
                            product_attribute_value_ids = []
                            if attribute_id.value_ids:
                                _logger.info("~~~~~~style~~~Value ids~~%r",attribute_id.value_ids)
                                to_add_id = False
                                for value in  attribute_id.value_ids:
                                    if value.name == prod.style:
                                        to_add_id = value
                                        _logger.info("~~style~~~~~ADD CUSTOM ID = %r",to_add_id)
                                        
                                        break
                                if not to_add_id:
                                    skip = False
                                    for exis_value in product_attr_data.get(attribute_id.id):
                                        if exis_value.name == prod.style:
                                            skip = True
                                            break
                                    if not skip:
                                        to_add_id = self.env['product.attribute.custom'].add_custom_value(attribute_id , prod.style)
                                        
                                
                                if to_add_id:
                                    product_attribute_value_ids += [to_add_id.id]
                                    
                                    
                                # _logger.info("``product_attribute_value_ids```````~~~~~~~~~ %r ", product_attribute_value_ids )

                            if product_attribute_value_ids:   
                                # _logger.info("~~~~~~~1~~~~%r~~~~~~~~~~",product_id.attribute_line_ids)  
                                exist_attr_line_id =  product_id.attribute_line_ids.search([('attribute_id', 'in', [attribute_id.id]),('product_tmpl_id', '=', product_id.id)], limit=1)
                                # _logger.info("~~~~~~~~2~~~%r~~~~~~~~~~",exist_attr_line_id)  
                                
                            
                                if exist_attr_line_id: 
                                    exist_attr_line_id.unlink() 
                                attr_line = self.env['product.template.attribute.line'].create({
                                    'attribute_id': attribute_id.id,
                                    'product_tmpl_id': product_id.id,
                                    'value_ids': [(6, 0, product_attribute_value_ids)],
                                })
                                # _logger.info("~~~~~added~~~~~~~~~~~~%r~~~~~~", attr_line)
                                
                                    
                            # _logger.info("~~product_attribute_value_ids~~~~~~%r~~~~~~attribute_line_ids~~~~~~%r~~~~~~~~~~~~~~~",product_attribute_value_ids , attribute_line_ids )
                            
                    ###################
                    # COLOR ATTRIBUTE #
                    ###################
                    
                    if prod.color:
                        attribute_id = product_attribute.search([("name", "=", "Color")], limit=1)
                        if attribute_id:
                            product_attribute_value_ids = []
                            if attribute_id.value_ids:
                                _logger.info("~~~~~~color~~~Value ids~~%r",attribute_id.value_ids)
                                to_add_id = False
                                for value in  attribute_id.value_ids:
                                    if value.name == prod.color:
                                        to_add_id = value
                                        _logger.info("~~COLOR~~~~~ADD CUSTOM ID = %r",to_add_id)
                                        
                                        break
                                if not to_add_id:
                                    skip = False
                                    for exis_value in product_attr_data.get(attribute_id.id):
                                        if exis_value.name == prod.color:
                                            skip = True
                                            break
                                    if not skip:
                                        to_add_id = self.env['product.attribute.custom'].add_custom_value(attribute_id , prod.color)
                                        
                                
                                if to_add_id:
                                    product_attribute_value_ids += [to_add_id.id]
                                    
                                # _logger.info("``product_attribute_value_ids```````~~~~~~~~~ %r ", product_attribute_value_ids )

                            if product_attribute_value_ids:   
                                # _logger.info("~~~~~~~1~~~~%r~~~~~~~~~~",product_id.attribute_line_ids)  
                                exist_attr_line_id =  product_id.attribute_line_ids.search([('attribute_id', 'in', [attribute_id.id]),('product_tmpl_id', '=', product_id.id)], limit=1)
                                # _logger.info("~~~~~~~~2~~~%r~~~~~~~~~~",exist_attr_line_id)  
                                
                            
                                if exist_attr_line_id: 
                                    exist_attr_line_id.unlink() 
                                attr_line = self.env['product.template.attribute.line'].create({
                                    'attribute_id': attribute_id.id,
                                    'product_tmpl_id': product_id.id,
                                    'value_ids': [(6, 0, product_attribute_value_ids)],
                                })
                                # _logger.info("~~~~~added~~~~~~~~~~~~%r~~~~~~", attr_line)
                                
                                    
                            # _logger.info("~~product_attribute_value_ids~~~~~~%r~~~~~~attribute_line_ids~~~~~~%r~~~~~~~~~~~~~~~",product_attribute_value_ids , attribute_line_ids )
                            
                    ######################
                    # MATERIAL ATTRIBUTE #
                    ######################            
                                    
                    if prod.material:
                        attribute_id = product_attribute.search([("name", "=", "Material")], limit=1)
                        if attribute_id:
                            product_attribute_value_ids = []
                            if attribute_id.value_ids:
                                to_add_id = False
                                for value in  attribute_id.value_ids:
                                    if value.name == prod.material:
                                        to_add_id = value
                                        break
                                if not to_add_id:
                                    skip = False
                                    for exis_value in product_attr_data.get(attribute_id.id):
                                        if exis_value.name == prod.material:
                                            skip = True
                                            break
                                    if not skip:
                                        to_add_id = self.env['product.attribute.custom'].add_custom_value(attribute_id , prod.material)
                                        # _logger.info("~~~~~~~ADD CUSTOM ID = %r",to_add_id)
                                
                                if to_add_id:
                                    product_attribute_value_ids += [to_add_id.id]
                                    
                                # _logger.info("``product_attribute_value_ids```````~~~~~~~~~ %r ", product_attribute_value_ids )

                            if product_attribute_value_ids:   
                                # _logger.info("~~~~~~~1~~~~%r~~~~~~~~~~",product_id.attribute_line_ids)  
                                exist_attr_line_id =  product_id.attribute_line_ids.search([('attribute_id', 'in', [attribute_id.id]),('product_tmpl_id', '=', product_id.id)], limit=1)
                                # _logger.info("~~~~~~~~2~~~%r~~~~~~~~~~",exist_attr_line_id)  
                                
                            
                                if exist_attr_line_id: 
                                    exist_attr_line_id.unlink() 
                                attr_line = self.env['product.template.attribute.line'].create({
                                    'attribute_id': attribute_id.id,
                                    'product_tmpl_id': product_id.id,
                                    'value_ids': [(6, 0, product_attribute_value_ids)],
                                })
                                # _logger.info("~~~~~added~~~~~~~~~~~~%r~~~~~~", attr_line)
                                
                                    
                            # _logger.info("~~product_attribute_value_ids~~~~~~%r~~~~~~attribute_line_ids~~~~~~%r~~~~~~~~~~~~~~~",product_attribute_value_ids , attribute_line_ids )lue_ids , attribute_line_ids )
                                
                    ##################
                    # SIZE ATTRIBUTE #
                    ##################
                                
                    if prod.size:
                        attribute_id = product_attribute.search([("name", "=", "Size")], limit=1)
                        if attribute_id:
                            product_attribute_value_ids = []
                            if attribute_id.value_ids:
                                to_add_id = False
                                for value in  attribute_id.value_ids:
                                    if value.name == prod.size:
                                        to_add_id = value
                                        break
                                if not to_add_id:
                                    skip = False
                                    for exis_value in product_attr_data.get(attribute_id.id):
                                        if exis_value.name == prod.size:
                                            skip = True
                                            break
                                    if not skip:
                                        to_add_id = self.env['product.attribute.custom'].add_custom_value(attribute_id , prod.size)
                                
                                if to_add_id:
                                    product_attribute_value_ids += [to_add_id.id]
                                    
                                # _logger.info("``product_attribute_value_ids```````~~~~~~~~~ %r ", product_attribute_value_ids )

                            if product_attribute_value_ids:   
                                # _logger.info("~~~~~~~1~~~~%r~~~~~~~~~~",product_id.attribute_line_ids)  
                                exist_attr_line_id =  product_id.attribute_line_ids.search([('attribute_id', 'in', [attribute_id.id]),('product_tmpl_id', '=', product_id.id)], limit=1)
                                # _logger.info("~~~~~~~~2~~~%r~~~~~~~~~~",exist_attr_line_id)  
                                
                            
                                if exist_attr_line_id: 
                                    exist_attr_line_id.unlink() 
                                attr_line = self.env['product.template.attribute.line'].create({
                                    'attribute_id': attribute_id.id,
                                    'product_tmpl_id': product_id.id,
                                    'value_ids': [(6, 0, product_attribute_value_ids)],
                                })
                            #     _logger.info("~~~~~added~~~~~~~~~~~~%r~~~~~~", attr_line)
                                
                                    
                            # _logger.info("~~product_attribute_value_ids~~~~~~%r~~~~~~attribute_line_ids~~~~~~%r~~~~~~~~~~~~~~~",product_attribute_value_ids , attribute_line_ids )

                    ##############################
                    # BACKING MATERIAL ATTRIBUTE #
                    ##############################
                                
                    if prod.backing_material:
                        attribute_id = product_attribute.search([("name", "=", "Backing Material")], limit=1)
                        if attribute_id:
                            product_attribute_value_ids = []
                            if attribute_id.value_ids:
                                to_add_id = False
                                for value in  attribute_id.value_ids:
                                    if value.name == prod.backing_material:
                                        to_add_id = value
                                        break
                                if not to_add_id:
                                    skip = False
                                    for exis_value in product_attr_data.get(attribute_id.id):
                                        if exis_value.name == prod.backing_material:
                                            skip = True
                                            break
                                    if not skip:
                                        to_add_id = self.env['product.attribute.custom'].add_custom_value(attribute_id , prod.backing_material)
                                
                                if to_add_id:
                                    product_attribute_value_ids += [to_add_id.id]
                                    
                                # _logger.info("``product_attribute_value_ids```````~~~~~~~~~ %r ", product_attribute_value_ids )

                            if product_attribute_value_ids:   
                                # _logger.info("~~~~~~~1~~~~%r~~~~~~~~~~",product_id.attribute_line_ids)  
                                exist_attr_line_id =  product_id.attribute_line_ids.search([('attribute_id', 'in', [attribute_id.id]),('product_tmpl_id', '=', product_id.id)], limit=1)
                                # _logger.info("~~~~~~~~2~~~%r~~~~~~~~~~",exist_attr_line_id)  
                                
                            
                                if exist_attr_line_id: 
                                    exist_attr_line_id.unlink() 
                                attr_line = self.env['product.template.attribute.line'].create({
                                    'attribute_id': attribute_id.id,
                                    'product_tmpl_id': product_id.id,
                                    'value_ids': [(6, 0, product_attribute_value_ids)],
                                })
                                # _logger.info("~~~~~added~~~~~~~~~~~~%r~~~~~~", attr_line)
                                
                                    
                            # _logger.info("~~product_attribute_value_ids~~~~~~%r~~~~~~attribute_line_ids~~~~~~%r~~~~~~~~~~~~~~~",product_attribute_value_ids , attribute_line_ids )lue_ids , attribute_line_ids )
                                    
                    ###################
                    # SHAPE ATTRIBUTE #
                    ###################               
                                
                    if prod.shape:
                        attribute_id = product_attribute.search([("name", "=", "Shape")], limit=1)
                        if attribute_id:
                            product_attribute_value_ids = []
                            if attribute_id.value_ids:
                                to_add_id = False
                                for value in  attribute_id.value_ids:
                                    if value.name == prod.shape:
                                        to_add_id = value
                                        break
                                if not to_add_id:
                                    skip = False
                                    for exis_value in product_attr_data.get(attribute_id.id):
                                        if exis_value.name == prod.shape:
                                            skip = True
                                            break
                                    if not skip:
                                        to_add_id = self.env['product.attribute.custom'].add_custom_value(attribute_id , prod.shape)
                                
                                if to_add_id:
                                    product_attribute_value_ids += [to_add_id.id]
                                    
                                # _logger.info("``product_attribute_value_ids```````~~~~~~~~~ %r ", product_attribute_value_ids )

                            if product_attribute_value_ids:   
                                # _logger.info("~~~~~~~1~~~~%r~~~~~~~~~~",product_id.attribute_line_ids)  
                                exist_attr_line_id =  product_id.attribute_line_ids.search([('attribute_id', 'in', [attribute_id.id]),('product_tmpl_id', '=', product_id.id)], limit=1)
                                # _logger.info("~~~~~~~~2~~~%r~~~~~~~~~~",exist_attr_line_id)  
                                
                            
                                if exist_attr_line_id: 
                                    exist_attr_line_id.unlink() 
                                attr_line = self.env['product.template.attribute.line'].create({
                                    'attribute_id': attribute_id.id,
                                    'product_tmpl_id': product_id.id,
                                    'value_ids': [(6, 0, product_attribute_value_ids)],
                                })
                            #     _logger.info("~~~~~added~~~~~~~~~~~~%r~~~~~~", attr_line)
                                
                                    
                            # _logger.info("~~product_attribute_value_ids~~~~~~%r~~~~~~attribute_line_ids~~~~~~%r~~~~~~~~~~~~~~~",product_attribute_value_ids , attribute_line_ids )
                     
                    ###############################
                    # CARE INSTRUCTIONS ATTRIBUTE #
                    ###############################    
                                
                    if prod.care_instructions:
                        attribute_id = product_attribute.search([("name", "=", "Care Instructions")], limit=1)
                        if attribute_id:
                            product_attribute_value_ids = []
                            if attribute_id.value_ids:
                                to_add_id = False
                                for value in  attribute_id.value_ids:
                                    if value.name == prod.care_instructions:
                                        to_add_id = value
                                        break
                                if not to_add_id:
                                    skip = False
                                    for exis_value in product_attr_data.get(attribute_id.id):
                                        if exis_value.name == prod.care_instructions:
                                            skip = True
                                            break
                                    if not skip:
                                        to_add_id = self.env['product.attribute.custom'].add_custom_value(attribute_id , prod.care_instructions)
                                
                                if to_add_id:
                                    product_attribute_value_ids += [to_add_id.id]
                                    
                                # _logger.info("``product_attribute_value_ids```````~~~~~~~~~ %r ", product_attribute_value_ids )

                            if product_attribute_value_ids:   
                                # _logger.info("~~~~~~~1~~~~%r~~~~~~~~~~",product_id.attribute_line_ids)  
                                exist_attr_line_id =  product_id.attribute_line_ids.search([('attribute_id', 'in', [attribute_id.id]),('product_tmpl_id', '=', product_id.id)], limit=1)
                                # _logger.info("~~~~~~~~2~~~%r~~~~~~~~~~",exist_attr_line_id)  
                                
                            
                                if exist_attr_line_id: 
                                    exist_attr_line_id.unlink() 
                                attr_line = self.env['product.template.attribute.line'].create({
                                    'attribute_id': attribute_id.id,
                                    'product_tmpl_id': product_id.id,
                                    'value_ids': [(6, 0, product_attribute_value_ids)],
                                })
                            #     _logger.info("~~~~~added~~~~~~~~~~~~%r~~~~~~", attr_line)
                                
                                    
                            # _logger.info("~~product_attribute_value_ids~~~~~~%r~~~~~~attribute_line_ids~~~~~~%r~~~~~~~~~~~~~~~",product_attribute_value_ids , attribute_line_ids )
                            
                _logger.info("~~~~~  Product Updated - %r  ~~~~~~", product_id)

            else:
                _logger.info("~~~~~  Product Not Found - %r  ~~~~~~", prod.sku)

        except Exception as e:
            _logger.info("Error While Mapping The Product Attributes --  %r  ", e)
            
            
            