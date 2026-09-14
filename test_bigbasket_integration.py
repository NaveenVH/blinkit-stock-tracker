import sys
import os
import firebase_setup
import crawler

sys.stdout.reconfigure(encoding='utf-8')

print("==========================================")
print("Testing BigBasket & Blinkit Integration")
print("==========================================")

# Sample BigBasket URL requested by user
bb_url = "https://www.bigbasket.com/pd/40372056/hot-wheels-jjl05-die-cast-car-el-segundo-coupe-clip-1-pc/?nc=cl-prod-list&t_pos_sec=1&t_pos_item=1&t_s=Experimotors+EL+Segundo+Coupe+Clip+Die+Cast+Toy+Car+For+3%252B+Years"

print("\n1. Testing BigBasket Link Parsing:")
res_bb = firebase_setup.parse_and_add_product(bb_url)
print("Result BB:", res_bb)

# Sample Blinkit Link
bk_url = "https://blinkit.com/prn/x/prid/787541"

print("\n2. Testing Blinkit Link Parsing:")
res_bk = firebase_setup.parse_and_add_product(bk_url)
print("Result BK:", res_bk)

print("\n3. Testing Active Monitors Retrieval:")
monitors = firebase_setup.get_active_monitors()
print(f"Total Active Monitors Found: {len(monitors)}")
for m in monitors:
    print(f" - [{m.get('source', 'blinkit').upper()}] Product: {m.get('product_name')} (ID: {m.get('product_id')}) at location: {m.get('pincode')}")

print("\n==========================================")
print("Integration Test Completed Successfully!")
print("==========================================")

