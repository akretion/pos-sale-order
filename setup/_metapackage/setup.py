import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-akretion-pos-sale-order",
    description="Meta package for akretion-pos-sale-order Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-pos_partial_payment',
        'odoo12-addon-pos_sale_order',
        'odoo12-addon-pos_sale_order_load',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 12.0',
    ]
)
