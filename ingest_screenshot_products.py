import firebase_setup

msg1 = "Check out this product on Blinkit - Hot Wheels Lil' Mad Die Cast Car https://blinkit.com/prn/x/prid/804832"
msg2 = "Check out this product on Blinkit - Hot Wheels Rapid Pulse Die Cast Car https://blinkit.com/prn/x/prid/804934"

print("Ingesting screenshot products...")
res1 = firebase_setup.parse_and_add_product(msg1)
print(f"[+] Product 1: {res1}")

res2 = firebase_setup.parse_and_add_product(msg2)
print(f"[+] Product 2: {res2}")

print("\nIngestion complete!")

