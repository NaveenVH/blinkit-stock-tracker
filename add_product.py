import argparse
import firebase_setup
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(
        description="Parse a Blinkit product link or message string and auto-add it to Firebase across all locations."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Raw message text or Blinkit URL (e.g. 'Check out this product on Blinkit - Hot Wheels Chop N Bloc Die Cast Car https://blinkit.com/prn/x/prid/787541')"
    )
    parser.add_argument(
        "--url", "-u",
        help="Blinkit Product URL"
    )

    args = parser.parse_args()
    input_text = args.text or args.url

    if not input_text:
        print("Error: Please provide a Blinkit message or URL string.")
        print("Example: python add_product.py \"Check out this product on Blinkit - Hot Wheels Chop N Bloc Die Cast Car https://blinkit.com/prn/x/prid/787541\"")
        sys.exit(1)

    print(f"Parsing input: {input_text}\n")
    result = firebase_setup.parse_and_add_product(input_text)

    if result:
        print("\n==================================================")
        print(" ✅ SUCCESS: Product Added / Active in Firebase!")
        print("==================================================")
        print(f"  Product ID:       {result['product_id']}")
        print(f"  Product Name:     {result['product_name']}")
        print(f"  Active Locations: {result['locations_count']}")
        print(f"  New Monitors:     {result['monitors_created']}")
        print("\nOn the next scheduled run (main.py), stock will be crawled for this product across all locations!")
    else:
        print("Failed to add product. Please check the input format.")

if __name__ == "__main__":
    main()
