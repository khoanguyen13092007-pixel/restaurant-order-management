# Chỉ mục test case tự động

Mỗi dòng là một unit test đã viết trong `tests/`. Khi điền Testing Document Template, dùng cùng mã TC để đối chiếu.

| Mã TC | Nội dung (theo tên test) | File |
|---|---|---|
| TC_AUTH_01 | login success redirects to dashboard | `tests/test_auth.py` |
| TC_AUTH_02 | wrong password rejected | `tests/test_auth.py` |
| TC_AUTH_03 | unknown user rejected with same message | `tests/test_auth.py` |
| TC_AUTH_04 | inactive account denied | `tests/test_auth.py` |
| TC_AUTH_05 | empty fields rejected | `tests/test_auth.py` |
| TC_AUTH_06 | password stored as hash | `tests/test_auth.py` |
| TC_AUTH_07 | logout clears session | `tests/test_auth.py` |
| TC_AUTH_08 | dashboard requires login | `tests/test_auth.py` |
| TC_AUTH_09 | wrong role gets 403 | `tests/test_auth.py` |
| TC_AUTH_10 | session is permanent for timeout | `tests/test_auth.py` |
| TC_AUTH_11 | each role lands on its own screen | `tests/test_auth.py` |
| TC_AUTH_12 | login page matches design | `tests/test_auth.py` |
| TC_FLOW_01 | csrf blocks post without token | `tests/test_flow.py` |
| TC_FLOW_02 | end to end | `tests/test_flow.py` |
| TC_KITCHEN_01 | only confirmed orders reach kitchen | `tests/test_kitchen.py` |
| TC_KITCHEN_02 | status flow | `tests/test_kitchen.py` |
| TC_KITCHEN_03 | cannot skip or go backwards | `tests/test_kitchen.py` |
| TC_KITCHEN_04 | ticket status follows items | `tests/test_kitchen.py` |
| TC_KITCHEN_05 | ready notification and served | `tests/test_kitchen.py` |
| TC_KITCHEN_06 | cancelled item not shown to kitchen | `tests/test_kitchen.py` |
| TC_KITCHEN_07 | kitchen model | `tests/test_kitchen.py` |
| TC_KITCHEN_08 | pages respect roles | `tests/test_kitchen.py` |
| TC_KITCHEN_09 | board lists done items and filters | `tests/test_kitchen.py` |
| TC_KITCHEN_10 | screen matches design | `tests/test_kitchen.py` |
| TC_KITCHEN_11 | dismiss banner marks served | `tests/test_kitchen.py` |
| TC_MENU_01 | search ignores case and accents | `tests/test_menu_tables.py` |
| TC_MENU_02 | filter by category | `tests/test_menu_tables.py` |
| TC_MENU_03 | create item validation | `tests/test_menu_tables.py` |
| TC_MENU_04 | sold out item not offered | `tests/test_menu_tables.py` |
| TC_MENU_05 | update price | `tests/test_menu_tables.py` |
| TC_MENU_06 | cannot delete item used in order | `tests/test_menu_tables.py` |
| TC_MENU_07 | delete category rules | `tests/test_menu_tables.py` |
| TC_MENU_08 | manage requires manager | `tests/test_menu_tables.py` |
| TC_MENU_09 | menu page for any staff | `tests/test_menu_tables.py` |
| TC_MENU_10 | manager edit panel and save | `tests/test_menu_tables.py` |
| TC_MENU_11 | manager screen matches design | `tests/test_menu_tables.py` |
| TC_ORDER_01 | create order with table | `tests/test_orders.py` |
| TC_ORDER_02 | totals include tax | `tests/test_orders.py` |
| TC_ORDER_03 | invalid quantity rejected | `tests/test_orders.py` |
| TC_ORDER_04 | edit and cancel item before cooking | `tests/test_orders.py` |
| TC_ORDER_05 | cannot edit item after kitchen started | `tests/test_orders.py` |
| TC_ORDER_06 | confirm sends ticket to kitchen | `tests/test_orders.py` |
| TC_ORDER_07 | new items on confirmed order get new ticket | `tests/test_orders.py` |
| TC_ORDER_08 | cancel order releases table | `tests/test_orders.py` |
| TC_ORDER_09 | cannot cancel order once cooking | `tests/test_orders.py` |
| TC_ORDER_10 | models follow class diagram | `tests/test_orders.py` |
| TC_ORDER_11 | customer places order at table | `tests/test_orders.py` |
| TC_ORDER_12 | customer adds to existing order of table | `tests/test_orders.py` |
| TC_ORDER_13 | customer order validation | `tests/test_orders.py` |
| TC_ORDER_14 | customer page needs no login | `tests/test_orders.py` |
| TC_ORDER_15 | duplicate submit creates one order | `tests/test_orders.py` |
| TC_ORDER_16 | duplicate customer submit creates one order | `tests/test_orders.py` |
| TC_ORDER_17 | order pages require staff role | `tests/test_orders.py` |
| TC_ORDER_18 | staff order is confirmed and sent to kitchen | `tests/test_orders.py` |
| TC_ORDER_19 | screen has cart and filters from design | `tests/test_orders.py` |
| TC_PAY_01 | compute totals | `tests/test_payment_reports.py` |
| TC_PAY_02 | discount validation | `tests/test_payment_reports.py` |
| TC_PAY_03 | preview does not change order | `tests/test_payment_reports.py` |
| TC_PAY_04 | pay cash with change releases table | `tests/test_payment_reports.py` |
| TC_PAY_05 | discount saved on order | `tests/test_payment_reports.py` |
| TC_PAY_06 | insufficient cash rejected | `tests/test_payment_reports.py` |
| TC_PAY_07 | cannot pay twice | `tests/test_payment_reports.py` |
| TC_PAY_08 | invalid method and unpayable orders | `tests/test_payment_reports.py` |
| TC_PAY_09 | invoice data | `tests/test_payment_reports.py` |
| TC_PAY_10 | cashier model handle payment | `tests/test_payment_reports.py` |
| TC_PAY_11 | revenue by day | `tests/test_payment_reports.py` |
| TC_PAY_12 | revenue by week and month | `tests/test_payment_reports.py` |
| TC_PAY_13 | best selling sorted by quantity | `tests/test_payment_reports.py` |
| TC_PAY_14 | report excludes unpaid and out of range | `tests/test_payment_reports.py` |
| TC_PAY_15 | report input validation | `tests/test_payment_reports.py` |
| TC_PAY_16 | pages respect roles | `tests/test_payment_reports.py` |
| TC_PAY_17 | find order by table | `tests/test_payment_reports.py` |
| TC_PAY_18 | cashier screen matches design | `tests/test_payment_reports.py` |
| TC_PAY_19 | report screen matches design | `tests/test_payment_reports.py` |
| TC_TABLE_01 | create and rename rules | `tests/test_menu_tables.py` |
| TC_TABLE_02 | assign marks occupied | `tests/test_menu_tables.py` |
| TC_TABLE_03 | move table | `tests/test_menu_tables.py` |
| TC_TABLE_04 | merge free table | `tests/test_menu_tables.py` |
| TC_TABLE_05 | merge table with other order merges orders | `tests/test_menu_tables.py` |
| TC_TABLE_06 | cannot delete busy or used table | `tests/test_menu_tables.py` |
| TC_TABLE_07 | pages respect roles | `tests/test_menu_tables.py` |
| TC_TABLE_08 | screen shows selected order and target | `tests/test_menu_tables.py` |
| TC_TABLE_09 | move and merge through the screen | `tests/test_menu_tables.py` |
| TC_TABLE_10 | manager saves table | `tests/test_menu_tables.py` |
