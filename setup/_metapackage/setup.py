import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-akretion-pos-sale-order",
    description="Meta package for akretion-pos-sale-order Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-pos_partial_payment',
        'odoo14-addon-pos_sale_order',
        'odoo14-addon-pos_sale_order_debug',
        'odoo14-addon-pos_sale_order_delivery',
        'odoo14-addon-pos_sale_order_load',
        'odoo14-addon-pos_sale_order_no_payment',
        'odoo14-addon-pos_sale_order_reference',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
