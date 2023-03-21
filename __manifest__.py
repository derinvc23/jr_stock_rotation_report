# -*- coding: utf-8 -*-

{
    'name': 'Stock Rotation excel report',
    'version': '10.0.1.1',
    'sequence':1,
    'category': 'Stock',
   
    
    'author': 'Jesus rodriguez',
    
    'depends': ['sale_stock','base','stock'],
    'data': [
        'wizard/jr_rotation_inventory_views.xml',
        'security/ir.model.access.csv',
        
    ],
  
    'installable': True,
    'application': True,
    'auto_install': False,
   
}


