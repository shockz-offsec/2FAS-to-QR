import qrcode
import json
import urllib.parse
from pathlib import Path
import sys

def load_backup(file_path):
    """Carga y valida el archivo de respaldo."""
    with open(file_path) as f:
        backup = json.load(f)
    if backup.get("schemaVersion") != 4:
        print("Error: 2FAS backup schema version not 4")
        sys.exit(1)
    return backup

def sanitize_filename(name):
    """Genera un nombre de archivo seguro."""
    return "".join(c for c in name if c.isalnum())

def generate_qr_codes(backup, output_dir):
    """Genera códigos QR y enlaces TOTP a partir del respaldo."""
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

        # Crear enlace TOTP
        link = (
            f'otpauth://totp/{name}:{account}?'
            f'secret={secret}&issuer={issuer}&algorithm={algorithm}&digits={digits}&period={period}'
        )
        links_list.append(link)

        # Crear y guardar el código QR
        filename = sanitize_filename(f'{service["name"]}_{account or "no_account"}_{issuer or "no_issuer"}')
        qrcode.make(link).save(f"{output_dir}/{filename}.png")

    return links_list

def save_links(links, output_file):
    """Guarda los enlaces TOTP en un archivo de texto."""
    with open(output_file, "w") as f:
        f.write("\n".join(links))

def main():
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <ruta_al_archivo_2fas>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = "./qrcodes"
    links_file = "./links.txt"

    backup = load_backup(input_file)
    links = generate_qr_codes(backup, output_dir)
    save_links(links, links_file)

    print(f"Códigos QR guardados en {output_dir}")
    print(f"Enlaces TOTP guardados en {links_file}")

if __name__ == "__main__":
    main()