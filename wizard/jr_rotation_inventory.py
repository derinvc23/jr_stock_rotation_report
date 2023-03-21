# -*- coding: utf-8 -*-


from cStringIO import StringIO
from datetime import datetime , timedelta,date
from openerp import models, fields, api, _
import xlwt
from xlwt import easyxf
import base64
import itertools
from operator import itemgetter
import operator
from dateutil.relativedelta import relativedelta


class dev_stock_inventory(models.TransientModel):
    _name = "jr.stock.inventory"

    @api.model
    def _get_company_id(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company',string='Company',required="1", default=_get_company_id)
    warehouse_ids = fields.Many2many('stock.warehouse',string='Warehouse')
    
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    bol_alm=fields.Boolean(string="Filtrar por almacen?")



    def last_day_m(self):
        last_act=self.end_date.replace(day=1,month=self.end_date.month+1)
        return last_act-timedelta(days=1)

    def last_day_m_int(self, date):
        if date.month!=12:
            last_act=date.replace(day=1,month=date.month+1)
            return last_act-timedelta(days=1)
        else:
            return date.replace(day=31,month=12)

    @api.multi
    def export_stock_ledger(self):
        workbook = xlwt.Workbook()
        filename = 'Stock Rotation Inventory.xls'
        # Style
        main_header_style = easyxf('font:height 400;pattern: pattern solid, fore_color gray25;'
                                   'align: horiz center;font: color black; font:bold True;'
                                   "borders: top thin,left thin,right thin,bottom thin")

        header_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz center;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")

        group_style = easyxf('font:height 200;pattern: pattern solid, fore_color gray25;'
                              'align: horiz left;font: color black; font:bold True;'
                              "borders: top thin,left thin,right thin,bottom thin")

        text_left = easyxf('font:height 150; align: horiz left;' "borders: top thin,bottom thin")
        text_right_bold = easyxf('font:height 200; align: horiz right;font:bold True;' "borders: top thin,bottom thin")
        text_right_bold1 = easyxf('font:height 200; align: horiz right;font:bold True;' "borders: top thin,bottom thin", num_format_str='0.00')
        text_center = easyxf('font:height 150; align: horiz center;' "borders: top thin,bottom thin")
        text_right = easyxf('font:height 150; align: horiz right;' "borders: top thin,bottom thin",
                            num_format_str='0.00')
        text_right1 = easyxf('font:height 150,colour red; align: horiz right;' "borders: top thin,bottom thin",
                            num_format_str='0.00')
        text_right2 = easyxf('font:height 150,colour blue; align: horiz right;' "borders: top thin,bottom thin",
                            num_format_str='0.00')

        if self.bol_alm:
            worksheet = []
            for l in range(0, len(self.warehouse_ids)):
                worksheet.append(l)
            work=0
            for warehouse_id in self.warehouse_ids:
                worksheet[work] = workbook.add_sheet(warehouse_id.name)
                for i in range(0, 9):
                    worksheet[work].col(i).width = 140 * 30

                worksheet[work].write_merge(0, 1, 0, 9, 'STOCK ROTATION', main_header_style)

               
                worksheet[work].write(4, 1, 'Warehouse', header_style)
                
                worksheet[work].write(4, 3, 'Start Date', header_style)
                worksheet[work].write(4, 4, 'End Date', header_style)
                worksheet[work].write(5, 3, self.start_date, text_center)
                worksheet[work].write(5, 4, self.end_date, text_center)



                
                worksheet[work].write(5, 1, warehouse_id.name, text_center)
                
                

            

                mes_ano=[]
            
                dif_month1=(int(fields.Datetime.from_string(self.end_date).year)-int(fields.Datetime.from_string(self.start_date).year))*12+int(fields.Datetime.from_string(self.end_date).month)-int(fields.Datetime.from_string(self.start_date).month)
                
                if dif_month1==0:
                    dif_month=1
                else:
                    dif_month=dif_month1

                for i in range(dif_month):
                    mes_ano.append(str((fields.Datetime.from_string(self.start_date) + relativedelta(months=i)).month)+"/"+str((fields.Datetime.from_string(self.start_date) + relativedelta(months=i)).year))

                c = 4
                r= 8
                for n in mes_ano:
                    worksheet[work].write(r, c, n, header_style)
                    c+=1
                    

            

                r= 9

                p_stock=[]
                data=[]
                for month in range(dif_month):
                    if fields.Datetime.from_string(self.start_date).month+month>12:
                        month1=month-(12-int(fields.Datetime.from_string(self.start_date).month))
                        year=fields.Datetime.from_string(self.start_date).year+1
                    else:
                        month1=int(fields.Datetime.from_string(self.start_date).month)+month
                        year=fields.Datetime.from_string(self.start_date).year
                    obj=self.env["sale.order"].search([
                        ("confirmation_date",">=",fields.Datetime.to_string(fields.Datetime.from_string(self.start_date).replace(day=1,month=int(month1),year=year))),
                        ("confirmation_date","<=",fields.Datetime.to_string(self.last_day_m_int(fields.Datetime.from_string((self.start_date)).replace(month=int(month1),year=year)))),
                
                        ])
                    
                    for ware in obj:
                        for pick in ware.picking_ids:
                            for lines in pick.move_lines:
                                if warehouse_id.lot_stock_id.id==lines.location_id.id:
                                    data.append([lines.product_id,lines.product_uom_qty,month])
                unique_p=[]
                for record1 in data:
                    if record1[0] not in unique_p:
                        unique_p.append(record1[0])

                for month in range(dif_month):
                    for record2 in unique_p:
                        stock=[]
                        for line2 in data:
                            if record2.id==line2[0].id and month==line2[2]:
                                stock.append(line2[1])
                        if stock:
                            p_stock.append([record2,sum(stock),month])
                        else:
                            p_stock.append([record2,0,month])

                unique_p_total=[]
                for record3 in p_stock:
                    if record3[0] not in unique_p_total:
                        unique_p_total.append(record3[0])


                c=2
                worksheet[work].write(r, c, "Producto", header_style)
                c=3
                worksheet[work].write(r, c, "Meta", header_style)

                c = 4
                for tag in range(dif_month):
                    worksheet[work].write(r, c, "Ventas", header_style)
                    c+=1

                
                
                    
                
                for month in range(dif_month):
                    r=10
                    for line in unique_p_total:
                        
                        for product in p_stock:

                            if line.id==product[0].id and product[2]==month and month==0:
                            
                                c=2
                                worksheet[work].write(r, c , line[0].display_name, text_right)
                                c=c+1
                                if line[0].meta_ids.filtered(lambda x:x.warehouse_id.lot_stock_id.id==warehouse_id.lot_stock_id.id):
                                    worksheet[work].write(r, c , line[0].meta_ids.filtered(lambda x:x.warehouse_id.lot_stock_id.id==warehouse_id.lot_stock_id.id)[0].meta, text_right)
                                    c=c+1
                                else:
                                    worksheet[work].write(r, c ,"sin definir",text_right)
                                    c=c+1
                                if line[0].meta_ids.filtered(lambda x:x.warehouse_id.lot_stock_id.id==warehouse_id.lot_stock_id.id):
                                    if product[1]<line[0].meta_ids.filtered(lambda x:x.warehouse_id.lot_stock_id.id==warehouse_id.lot_stock_id.id)[0].meta:
                                        worksheet[work].write(r, c, product[1], text_right1)
                                        r+=1
                                    else:
                                        worksheet[work].write(r, c, product[1], text_right2)
                                        r+=1
                                else:
                                    worksheet[work].write(r, c, product[1], text_right)
                                    r+=1

                            elif line.id==product[0].id and product[2]==month and month!=0:
                            
                                c=4+month

                                if line[0].meta_ids.filtered(lambda x:x.warehouse_id.lot_stock_id.id==warehouse_id.lot_stock_id.id):
                                    if product[1]<line[0].meta_ids.filtered(lambda x:x.warehouse_id.lot_stock_id.id==warehouse_id.lot_stock_id.id)[0].meta:
                                        worksheet[work].write(r, c, product[1], text_right1)
                                        r+=1
                                    else:
                                        worksheet[work].write(r, c, product[1], text_right2)
                                        r+=1
                                else:
                                    worksheet[work].write(r, c, product[1], text_right)
                                    r+=1
                    



                work+=1
        else:
            worksheet = []
        
            worksheet.append(1)
            work=0
            worksheet[work] = workbook.add_sheet("Rotation")
            
            
            for i in range(0, 9):
                worksheet[work].col(i).width = 140 * 30

            worksheet[work].write_merge(0, 1, 0, 9, 'STOCK ROTATION', main_header_style)

            
            worksheet[work].write(4, 3, 'Start Date', header_style)
            worksheet[work].write(4, 4, 'End Date', header_style)
            worksheet[work].write(5, 3, self.start_date, text_center)
            worksheet[work].write(5, 4, self.end_date, text_center)



            
            
            
            

        

            mes_ano=[]
        
            dif_month1=(int(fields.Datetime.from_string(self.end_date).year)-int(fields.Datetime.from_string(self.start_date).year))*12+int(fields.Datetime.from_string(self.end_date).month)-int(fields.Datetime.from_string(self.start_date).month)
            
            if dif_month1==0:
                dif_month=1
            else:
                dif_month=dif_month1

            for i in range(dif_month):
                mes_ano.append(str((fields.Datetime.from_string(self.start_date) + relativedelta(months=i)).month)+"/"+str((fields.Datetime.from_string(self.start_date) + relativedelta(months=i)).year))

            c = 4
            r= 8
            for n in mes_ano:
                worksheet[work].write(r, c, n, header_style)
                c+=1
                

        

            r= 9

            p_stock=[]
            data=[]
            for month in range(dif_month):
                if fields.Datetime.from_string(self.start_date).month+month>12:
                    month1=month-(12-int(fields.Datetime.from_string(self.start_date).month))
                    year=fields.Datetime.from_string(self.start_date).year+1
                else:
                    month1=int(fields.Datetime.from_string(self.start_date).month)+month
                    year=fields.Datetime.from_string(self.start_date).year
                obj=self.env["sale.order"].search([
                    ("confirmation_date",">=",fields.Datetime.to_string(fields.Datetime.from_string(self.start_date).replace(day=1,month=int(month1),year=year))),
                    ("confirmation_date","<=",fields.Datetime.to_string(self.last_day_m_int(fields.Datetime.from_string((self.start_date)).replace(month=int(month1),year=year)))),
            
                    ])
                
                for ware in obj:
                    for pick in ware.picking_ids:
                        for lines in pick.move_lines:
                            
                            data.append([lines.product_id,lines.product_uom_qty,month])
            unique_p=[]
            for record1 in data:
                if record1[0] not in unique_p:
                    unique_p.append(record1[0])

            for month in range(dif_month):
                for record2 in unique_p:
                    stock=[]
                    for line2 in data:
                        if record2.id==line2[0].id and month==line2[2]:
                            stock.append(line2[1])
                    if stock:
                        p_stock.append([record2,sum(stock),month])
                    else:
                        p_stock.append([record2,0,month])

            unique_p_total=[]
            for record3 in p_stock:
                if record3[0] not in unique_p_total:
                    unique_p_total.append(record3[0])


            c=2
            worksheet[work].write(r, c, "Producto", header_style)
            c=3
            worksheet[work].write(r, c, "Meta", header_style)

            c = 4
            for tag in range(dif_month):
                worksheet[work].write(r, c, "Ventas", header_style)
                c+=1

            
            
                
            
            for month in range(dif_month):
                r=10
                for line in unique_p_total:
                    
                    for product in p_stock:

                        if line.id==product[0].id and product[2]==month and month==0:
                        
                            c=2
                            worksheet[work].write(r, c , line[0].display_name, text_right)
                            c=c+1
                            worksheet[work].write(r, c , line[0].limit_sale_g, text_right)
                            c=c+1
                            if line[0].limit_sale_g:
                                if product[1]<line[0].limit_sale_g:
                                    worksheet[work].write(r, c, product[1], text_right1)
                                    r+=1
                                else:
                                    worksheet[work].write(r, c, product[1], text_right2)
                                    r+=1
                            else:
                                worksheet[work].write(r, c, product[1], text_right)
                                r+=1

                        elif line.id==product[0].id and product[2]==month and month!=0:
                        
                            c=4+month

                            if line[0].limit_sale_g:
                                if product[1]<line[0].limit_sale_g:
                                    worksheet[work].write(r, c, product[1], text_right1)
                                    r+=1
                                else:
                                    worksheet[work].write(r, c, product[1], text_right2)
                                    r+=1
                            else:
                                worksheet[work].write(r, c, product[1], text_right)
                                r+=1
                    


            

        fp = StringIO()
        workbook.save(fp)
        export_id = self.env['jr.rotation.inventory.excel'].create(
            {'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
        fp.close()

        return {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'jr.rotation.inventory.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }



class dev_stock_inventory_excel(models.TransientModel):
    _name = "jr.rotation.inventory.excel"

    excel_file = fields.Binary('Excel Report')
    file_name = fields.Char('Excel File')


class ProductProduct(models.Model):
    _inherit = "product.product"

    meta_ids = fields.One2many(related='product_tmpl_id.meta_ids')
    limit_sale_g = fields.Float(related='product_tmpl_id.limit_sale_g')
    

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    
    limit_sale_g = fields.Float(string='Meta mensual Global')
    meta_ids=fields.One2many("meta.warehouse","product_tmpl_id")

class Stockmeta(models.Model):
    _name="meta.warehouse"

    warehouse_id=fields.Many2one('stock.warehouse',string='Warehouse')
    meta=fields.Float(string="Meta")
    product_tmpl_id=fields.Many2one("product.template")
