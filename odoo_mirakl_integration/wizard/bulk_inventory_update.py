from asyncio.log import logger
from odoo import fields,api, _, models
# from pandas import *
import base64
# from IPython.display import display
import datetime
import json
from xlsxwriter import Workbook
# import pandas as pd    
import csv
import requests
class BulkInventoryUpdate(models.TransientModel):
    _name = 'bulk.inventory.update'
    _description = 'Bulk Inventory Update'

    market_ids = fields.Many2many('shop.integrator', string='Marketplaces',required=True)


    def update_inventory_csv(self):
        logger.info(_('Method called for inventory Update'))
        selected_records = self.env.context.get('selected_record')

        etl_warehouse = self.env['marketplace.warehouse'].search([('warehouse_code','=','ETL')])
        cdisc_warehouse = self.env['marketplace.warehouse'].search([('warehouse_code','=','CDISC')])
        if len(selected_records):
            records = self.env['warehouse.inventory'].browse(selected_records)
            cdisc_reords = self.env['warehouse.inventory'].search(['&',('create_date', '>=', datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')),('create_date', '<=',datetime.datetime.now().strftime('%Y-%m-%d 23:23:59')),('warehouse_id','=',cdisc_warehouse.id)])
            inventory_data = []
            merged_sku = []
            # for etl_record in records:
            for cdisc_record in cdisc_reords:
                etl_record = self.env['warehouse.inventory'].search(['&',('create_date', '>=', datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')),('create_date', '<=',datetime.datetime.now().strftime('%Y-%m-%d 23:23:59')),('warehouse_id','=',etl_warehouse.id),('product_id','=',cdisc_record.product_id)],limit=1)
                if etl_record and cdisc_record.product_id not in merged_sku:
                    inventory_data.append({'sku': cdisc_record.product_id, 'quantity': cdisc_record.available_stock_count +  etl_record.available_stock_count})
                    merged_sku.append(cdisc_record.product_id)
                elif cdisc_record.product_id not in merged_sku:
                    inventory_data.append({'sku': cdisc_record.product_id, 'quantity': cdisc_record.available_stock_count})
                    merged_sku.append(cdisc_record.product_id)
                    
            for record in records:
                etl_record = self.env['warehouse.inventory'].search(['&',('create_date', '>=', datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')),('create_date', '<=',datetime.datetime.now().strftime('%Y-%m-%d 23:23:59')),('warehouse_id','=',cdisc_warehouse.id),('product_id','=',record.product_id)],limit=1)
                if etl_record and etl_record.product_id not in merged_sku:
                    inventory_data.append({'sku': record.product_id, 'quantity': record.available_stock_count +  etl_record.available_stock_count})
                    merged_sku.append(cdisc_record.product_id)
                elif record.product_id not in merged_sku:
                    inventory_data.append({'sku': record.product_id, 'quantity': record.available_stock_count})
                    merged_sku.append(record.product_id)

            for shop in self.market_ids:
                self.send_api_call(shop,inventory_data,records)


    def send_api_call(self,shop,inventory_data,records):
        product_codes = [record.get('sku') for record in inventory_data]
        products = self.env['product.product'].search([('default_code','in', product_codes)])
        barcodes = ['0' + str(record.barcode) for record in products]
        call = shop.shop_url+"/api/offers/export?include_inactive_offers=true"
        if shop.shop_id:
            call += '&shop_id=' + shop.shop_id
        response_data = False
        try:
            response_data = requests.get(call,headers={'Authorization': shop.api_key,'Accept': 'application/csv'})
        except Exception as ex:
            logger.info(_(ex))
        if response_data:
            new_list = []
            updated_data = []
            with open("inventory.csv", "w") as my_empty_csv:
                pass 
            content = response_data.content.decode('utf-8')
            cr = csv.reader(content.splitlines(), delimiter=',')

            list_data = list(cr)
            qty_index = list_data[0][0].split(';').index('quantity')
            sku_index = list_data[0][0].split(';').index('shop-sku')
            update_index = None
            count = 1
            excluded_shop = ['Home24 DE','Conforama','But']
            for row in list_data:
                sku = row[0].split(';')[sku_index] if sku_index else False
                sku = sku.replace('"','')
                inventory_records = self.env['warehouse.inventory'].search([('id','in', records.ids)])
                if sku in product_codes :


                    #For shops other than adeo
                    for record in inventory_data:
                        if record.get('sku') == sku:
                            qty = 0

                            if sku.startswith("LBU") and shop.name in excluded_shop:
                                qty = record.get('quantity')
                            split_data = row[0].split(';')
                            split_data[qty_index] = '"' + str(record.get('quantity'))  + '"'

                            #Set quantity to zero based on shop configuration
                            if record.get('quantity') and record.get('quantity') >= shop.min_qty_to_zero:
                                qty = record.get('quantity')
                            else:
                                logger.info("Product %s with %s quantity found to set quantity as zero",sku,qty)

                            updated_data.append({'sku': sku, 'quantity': qty,'leadtime-to-ship': shop.lead_time_to_ship,'update-delete': 'update' })
                #For Adeo

                if sku in barcodes:
                    for record in inventory_records:
                        if '0' + str(record.odoo_product_id.barcode) == sku:
                            qty = 0

                            if sku.startswith("LBU") and shop.name in excluded_shop:
                                qty = record.get('quantity')
                            split_data = row[0].split(';')
                            split_data[qty_index] = '"' + str(record.available_stock_count)  + '"'

                            #Set quantity to zero based on shop configuration
                            if record.available_stock_count and record.available_stock_count >= shop.min_qty_to_zero:
                                qty = record.available_stock_count
                            else:
                                logger.info("Product %s with %s quantity found to set quantity as zero",sku,qty)

                            updated_data.append({'sku': sku, 'quantity': qty,'leadtime-to-ship': shop.lead_time_to_ship, 'update-delete': 'update'})


            
            # Prepare Excel file from dictonary Data
            logger.info(updated_data)
            df = pd.DataFrame.from_dict(updated_data)
            df.to_excel('inventory1.xlsx', index = None, header=True)
            
            #open file to attach in api call
            files = {'file': open('inventory1.xlsx','rb')}
            post_call = shop.shop_url + '/api/offers/imports'
            if shop.shop_id:
                post_call += '?shop_id=' + shop.shop_id
                logger.info("Shop inventory update called with shop Id %s for %s", shop.shop_id,shop.name)
            post_data_res = None
            if len(updated_data) > 0:
                try:
                    logger.info("Post Api call")
                    headers={'Authorization': shop.api_key,'Accept': 'application/json'}
                    # post_data_res =  requests.post(post_call,headers=headers, files=files, data= {'import_mode' : 'NORMAL'}).json()
                    logger.info(post_data_res)
                    excel_file = self.open_target_file()
                    encoded_excel = base64.b64encode(excel_file)
                    inventory_records = self.env['warehouse.inventory'].search([('id','in',records.ids)])
                    for inventory_record in inventory_records:

                        #Find if sku is updated via process or not
                        updated_sku = [data.get('sku') for data in updated_data]
                        if inventory_record.product_id in updated_sku or '0' + str(inventory_record.odoo_product_id.barcode) in updated_sku:
                            attachment_data = {
                                'name':'inventory_' + shop.name + '_' + str(datetime.datetime.now().date()),
                                'datas':encoded_excel,
                                'res_model':"warehouse.inventory",
                                'res_id': inventory_record.id,
                            }
                            self.env['ir.attachment'].create(attachment_data)
                    if post_data_res and post_data_res.get('import_id'):
                        #Check if file is successfully process in mirakl shop or not
                        import_id = post_data_res.get('import_id')
                        import_url = shop.shop_url+"/api/offers/imports/"+ str(import_id) + "/error_report"
                        try:
                            import_response = requests.get(import_url,headers={'Authorization': shop.api_key,'Accept': 'application/octet-stream'}).json()
                            logger.info(import_response)
                            if import_response.get('status'):
                                if import_response.get('status') == 404: #If file is successfully imported api will return 404
                                    logger.info(_("File Processed successfully. for %s "),shop.name)
                                    excel_file = self.open_target_file()
                                    encoded_excel = base64.b64encode(excel_file)
                                    inventory_records = self.env['warehouse.inventory'].search([('id','in',records.ids)])
                                    for inventory_record in inventory_records:

                                        #Find if sku is updated via process or not
                                        updated_sku = [data.get('sku') for data in updated_data]
                                        if inventory_record.product_id in updated_sku or inventory_record.odoo_product_id.barcode in updated_sku:
                                            attachment_data = {
                                                'name':'inventory_' + shop.name + '_' + str(datetime.datetime.now().date()),
                                                'datas':encoded_excel,
                                                'res_model':"warehouse.inventory",
                                                'res_id': inventory_record.id,
                                            }
                                            self.env['ir.attachment'].create(attachment_data)
                                            inventory_record.write({'last_updated_date': datetime.datetime.now() })

                                    self.update_odoo_markets_quantity(shop,product_codes,updated_data,barcodes)
                        except Exception as err:
                            logger.info("Error in File Data")
                    elif post_data_res:
                        #Log Error in Server
                        status = post_data_res.get('status')
                        if status and post_data_res.get('message'):
                            logger.info(_("%s in %s",post_data_res.get('message'),shop.name))

                except Exception as err:
                    logger.info(_(err))
            else:
                logger.info("No data matched to send to api skipping Api call for %s", shop.name)
        
        else:
            logger.info(_('Did not get data from get api'))
            
    def open_target_file(self):
        with open('inventory1.xlsx',"rb") as excel_file:
            return excel_file.read()

    def update_odoo_markets_quantity(self,shop,product_codes,excel_dict,barcodes):
        barcodes = [barcode[1:] for barcode in barcodes]
        products = self.env['product.product'].search(['|',('default_code','in', product_codes),('barcode','in',barcodes)])
        for product in products:
            for data in excel_dict:
                if product.default_code == data.get('sku') or product.barcode == data.get('sku')[1:]:
                    shop_stock = self.env['mirakl.stock'].search([('odoo_product_id', '=', product.id), ('shop_id','=',shop.id)])
                    shop_offer = self.env['mirakl.offers'].search([('product_id', '=', product.id), ('shop_id','=',shop.id)])
                    shop_stock.quantity = shop_offer.quantity = data.get('quantity')
                    shop_stock.last_updated_date = shop_offer.offer_update_date = datetime.datetime.now()



            
    




    
