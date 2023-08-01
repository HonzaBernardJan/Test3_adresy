import os
import zipfile
import requests
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import shutil
import csv
import subprocess

def download_and_extract_zip(url, output_directory):
    response = requests.get(url)
    zip_file_path = os.path.join(output_directory, "UI_OBEC.zip")
    with open(zip_file_path, "wb") as zip_file:
        zip_file.write(response.content)

    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(output_directory)
    os.remove(zip_file_path)
    print("Soubor byl úspěšně stažen a rozbalen.")

def get_obec_kod_from_nazev_obce(nazev_obce, csv_file_path, callback):
    df = pd.read_csv(csv_file_path, sep=";", encoding="cp1250")
    selected_row = df[df["NAZEV"] == nazev_obce]

    if not selected_row.empty:
        obec_kod = selected_row.iloc[0]["KOD"].astype(str)  # Převedeme na řetězec
        callback(obec_kod)
    else:
        print("Název obce nebyl nalezen.")
        callback(None)

def select_output_directory():
    root = tk.Tk()
    root.withdraw()
    output_directory = ""

    def open_dialog():
        nonlocal output_directory
        output_directory = filedialog.askdirectory(title="Vyberte složku pro uložení nového CSV souboru")
        root.quit()

    root.after(0, open_dialog)
    root.mainloop()
    return output_directory

def process_obec():
    url = "https://www.cuzk.cz/CUZK/media/CiselnikyISUI/UI_OBEC/UI_OBEC.zip?ext=.zip"
    output_directory = select_output_directory()

    download_and_extract_zip(url, output_directory)

    csv_file_path = os.path.join(output_directory, "UI_OBEC.csv")

    def obec_callback(obec_kod):
        if obec_kod is not None:
            output_txt_file = os.path.join(output_directory, f"kod_obce_{nazev_obce}.txt")
            with open(output_txt_file, mode="w", encoding="utf-8") as txt_file:
                txt_file.write(f"Kód obce {nazev_obce}: {obec_kod}")
            print(f"Kód obce {nazev_obce}: {obec_kod} byl zapsán do souboru {output_txt_file}.")
            nazev_ulice_casti = input("Zadejte název ulice nebo části obce: ")
            process_csv(output_directory, obec_kod, nazev_ulice_casti)
            os.remove(output_txt_file)  # Odstranit textový soubor
            shutil.rmtree(os.path.join(output_directory, "CSV"))  # Odstranit složku CSV
            os.remove(csv_file_path)  # Odstranit původní CSV soubor

    nazev_obce = input("Zadejte název obce: ")
    get_obec_kod_from_nazev_obce(nazev_obce, csv_file_path, obec_callback)

def process_csv(output_directory, kod_obce, nazev_ulice_casti):
    url = "https://vdp.cuzk.cz/vymenny_format/csv/20230630_OB_ADR_csv.zip"
    download_and_extract_zip(url, output_directory)

    csv_subdirectory = os.path.join(output_directory, "CSV")
    for filename in os.listdir(csv_subdirectory):
        if str(kod_obce) in filename:  # Převedeme na řetězec a porovnáme
            csv_file_path = os.path.join(csv_subdirectory, filename)
            break
    else:
        print(f"Soubor s kódem obce {kod_obce} nebyl nalezen v podsložce CSV.")
        exit(1)

    adresy = []
    with open(csv_file_path, newline="", encoding="cp1250") as csvfile:
        csv_reader = csv.DictReader(csvfile, delimiter=";")

        for row in csv_reader:
            obec = row.get("Název obce") or row.get("Název MOMC") or row.get("Název obvodu Prahy")
            ulice_from_csv = row.get("Název ulice") or row.get("Název části obce") or row.get("Název obvodu Prahy")
            typ_so = row.get("Typ SO")
            cp = row.get("Číslo popisné") or row.get("Číslo domovní") or row.get("Číslo orientační")
            psc = row.get("PSČ") or row.get("PSO")

            if ulice_from_csv and nazev_ulice_casti.lower() in ulice_from_csv.lower() and cp:
                address = f"{ulice_from_csv} {typ_so} {cp}, {obec} {psc}"
                adresy.append(address)

    if adresy:
        for address in adresy:
            print(address)

        csv_output_file = os.path.join(output_directory, f"adresy_{nazev_ulice_casti}.csv")
        with open(csv_output_file, mode="w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["Adresa"]
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csv_writer.writeheader()

            for adresa in adresy:
                csv_writer.writerow({"Adresa": adresa})

        print(f"Adresy byly zapsány do souboru {csv_output_file}.")
        subprocess.Popen(["notepad.exe", csv_output_file])  # Otevřít CSV soubor v Poznámkovém bloku
    else:
        print("Pro zadaný název nebyly nalezeny žádné adresy.")

if __name__ == "__main__":
    process_obec()
