import argparse
import firebase_setup
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(
        description="Parse a Blinkit product link or message string and toggle/auto-add it to Firebase."
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
        print(" ✅ SUCCESS: Product Updated in Firebase!")
        print("==================================================")
        print(f"  Product ID:       {result['product_id']}")
        print(f"  Product Name:     {result['product_name']}")
        print(f"  isActive Status:  {result.get('isActive')}")
        if result.get('toggled'):
            print(f"  Action:           TOGGLED ({result.get('status_label')})")
        else:
            print(f"  Active Locations: {result.get('locations_count', 1)}")
            print(f"  New Monitors:     {result.get('monitors_created', 0)}")
        print("\nChanges saved to Firebase!")
    else:
        print("Failed to process product link. Please check input format.")

if __name__ == "__main__":
    main()
