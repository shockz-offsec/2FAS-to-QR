import qrcode
import json
import urllib.parse
from pathlib import Path
import sys

def load_backup(file_path):
    """Load and validate the backup file."""
    with open(file_path) as f:
        backup = json.load(f)
    if backup.get("schemaVersion") != 4:
        print("Error: 2FAS backup schema version not 4")
        sys.exit(1)
    return backup

def sanitize_filename(name):
    """Generate a safe filename by removing invalid characters."""
    return "".join(c for c in name if c.isalnum())

def generate_qr_codes(backup, output_dir):
    """Generate QR codes and TOTP links from the backup."""
    links_list = []
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for service in backup["services"]:
        name = urllib.parse.quote_plus(service["name"], safe='')
        account = urllib.parse.quote_plus(service["otp"].get("account", ""), safe='')
        secret = urllib.parse.quote_plus(service["secret"], safe='')
        issuer = urllib.parse.quote_plus(service["otp"].get("issuer", ""), safe='')
        algorithm = urllib.parse.quote_plus(service["otp"]["algorithm"], safe='')
        digits = service["otp"]["digits"]
        period = service["otp"]["period"]

        # Build the TOTP link
        link = (
            f'otpauth://totp/{name}:{account}?'
            f'secret={secret}&issuer={issuer}&algorithm={algorithm}&digits={digits}&period={period}'
        )
        links_list.append(link)

        # Create and save the QR code
        filename = sanitize_filename(f'{service["name"]}_{account or "no_account"}_{issuer or "no_issuer"}')
        qrcode.make(link).save(f"{output_dir}/{filename}.png")

    return links_list

def save_links(links, output_file):
    """Save TOTP links to a text file."""
    with open(output_file, "w") as f:
        f.write("\n".join(links))

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_2fas_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = "./qrcodes"
    links_file = "./links.txt"

    backup = load_backup(input_file)
    links = generate_qr_codes(backup, output_dir)
    save_links(links, links_file)

    print(f"QR codes saved to {output_dir}")
    print(f"TOTP links saved to {links_file}")

if __name__ == "__main__":
    main()