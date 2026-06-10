- user

* id pk
* username varchar(255)\*
* password varchar(255)\*
* profile varchar(255)
* status varchar(255) [pending, rejected, approve]
* type varchar(255) [admin, student]

- shop

* id pk
* name varchar(255)\*
* address varchar(255)\*
* logo varchar(255)
* description varchar(500)
* user_id fk\*

- category

* id pk
* name varchar(255)\*
* remark varchar(255)
* user_id fk\*

- product

* id pk
* name varchar(255)\*
* category_id fk\*
* cost decimal(10, 2) [0]
* price decimal(10, 2) [0]
* stock decimal(10, 2) [0]
* image varchar(255)
* remark varchar(255)
* user_id fk\*

+payment_method

- id pk
- name varchar(255)\*
- remark varchar(255)
- user_id fk\*

* sale

- id pk
- shop_id fk\*
- user_id fk\*
- payment_method fk\*
- sale_date datetime date time\* [now]
- total decimal (10, 2)\* [0]
- discount_pct int\* [0]
- discount_amount (10, 2)\* [0]
- paid_amount decimal (10, 2)\* [0]

* sale_item

- id pk
- user_id fk\*
- sale_id fk\*
- product_id fk\*
- qty int\*
- price decimal(10, 2) [0]
