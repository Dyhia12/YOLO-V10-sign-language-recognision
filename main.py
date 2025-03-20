import os
import re
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import threading
import time

# Fonction pour redimensionner l'image avec YOLO
def redimensioner_YOLO(img_source: str):
    import cv2
    image = cv2.imread(img_source)
    resized_image = cv2.resize(image, (640, 640))
    cv2.imwrite(img_source, resized_image)

# Fonction pour afficher un dialogue de barre de progression
def show_progress_dialog(root):
    progress_dialog = tk.Toplevel(root)
    progress_dialog.title("Prédiction en cours")
    progress_dialog.geometry("300x100")

    label = tk.Label(progress_dialog, text="Prédiction en cours, veuillez patienter...")
    label.pack(pady=10)

    progress_bar = ttk.Progressbar(progress_dialog, orient="horizontal", mode="indeterminate", length=200)
    progress_bar.pack(pady=10)
    progress_bar.start()

    return progress_dialog, progress_bar

# Fonction pour rechercher et afficher l'image prédite
def afficher_image_predite(img_path, img_label):

    # Attendre 3 secondes
    #time.sleep(5)
    cleaned_img_path = re.sub(r'\x1b\[[0-9;]*m', '', img_path)
    cleaned_img_path = cleaned_img_path.strip()
    # Vérifier si l'image existe
    if img_path:
        #print(f'L\'image est trouvée à {img_path}')
        image = Image.open(img_path)
        image = image.resize((400, 400))  # Redimensionner pour l'affichage
        img = ImageTk.PhotoImage(image)

        img_label.config(image=img)
        img_label.image = img  # Mise à jour de l'image affichée
    else:
        #print(f'Erreur : L\'image n\'a pas été trouvée à {img_path}')
        messagebox.showerror("Erreur", "L'image prédite n'a pas été trouvée.")

# Fonction pour fermer la boîte de dialogue de progression dans le thread principal
def close_progress_dialog(root, progress_dialog):
    root.after(0, progress_dialog.destroy)

# Fonction pour effectuer la prédiction YOLO dans un thread séparé
def predict_image(img_path, modele_path, img_label, root):
    import re

    try:
        # Redimensionner l'image
        redimensioner_YOLO(img_path)

        # # Commande YOLO
        # command = f"yolo task=detect mode=predict model={modele_path} conf=0.04 source={img_path} imgsz=640"
        #
        # # Exécuter la prédiction
        # process = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)

        # Construire la commande comme une liste d'arguments
        command = [
            "yolo",
            "task=detect",
            "mode=predict",
            f"model={modele_path}",
            "conf=0.04",
            f"source={img_path}",
            "imgsz=640"
        ]

        # # Exécuter la commande
        # process = subprocess.run(command, check=True, text=True, capture_output=True)
        #
        # # Vérifier la sortie
        # if process.returncode == 0:
        #     print("Prédiction terminée avec succès.")
        # else:
        #     print(f"Erreur pendant la prédiction : {process.stderr}")

        try:
            # Exécuter la commande
            process = subprocess.run(command, check=True, text=True, capture_output=True)

            time.sleep(5)
            # Vérifier la sortie
            if process.returncode == 0:
                messagebox.showinfo("Succès", "Prédiction terminée avec succès.")
            else:
                messagebox.showerror("Erreur", f"Erreur pendant la prédiction : {process.stderr}")
        except subprocess.CalledProcessError as e:
            # Afficher une erreur si la commande échoue
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la prédiction.\n{e.stderr}")

        # Nettoyer la sortie de la commande pour enlever les séquences d'échappement ANSI
        stdout_cleaned = re.sub(r'\x1b\[[0-9;]*m', '', process.stdout)
        #print(f"Sortie nettoyée : {stdout_cleaned}")

        match = re.search(r"Results saved to (.*)", stdout_cleaned)
        if match:
            result_dir = match.group(1).strip()  # Extraire le chemin du répertoire de résultats
            #print(f"Répertoire des résultats : {result_dir}")

            # Extraire le nom de l'image source
            img_name = os.path.basename(img_path)

            # Construire le chemin complet de l'image prédite
            predicted_image_path = os.path.join(result_dir, img_name)
            #print(f"Chemin complet de l'image prédite : {predicted_image_path}")

            # Afficher l'image prédite après exécution de YOLO
            afficher_image_predite(predicted_image_path, img_label)
        else:
            pass
            # print("Chemin de l'image prédite non trouvé dans la sortie.")

    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue lors de la prédiction.\n{e.stderr}")
    finally:
        # Fermer la boîte de dialogue de progression dans le thread principal
        close_progress_dialog(root, progress_dialog)

# Fonction pour démarrer la prédiction dans un thread séparé
def start_prediction(img_path, modele_path, img_label, root):
    global progress_dialog
    progress_dialog, progress_bar = show_progress_dialog(root)
    modele_path = 'bestASL.pt'

    # Lancer la prédiction dans un thread séparé pour ne pas bloquer l'interface
    prediction_thread = threading.Thread(target=predict_image, args=(img_path, modele_path, img_label, root))
    prediction_thread.start()

# Fonction pour importer une image
def import_image(tab_control):
    img_path = filedialog.askopenfilename(title="Choisir une image", filetypes=[("Images", "*.jpg *.png")])

    if img_path:
        tab = ttk.Frame(tab_control)
        tab_control.add(tab, text=os.path.basename(img_path))

        # Afficher l'image importée
        image = Image.open(img_path)
        image = image.resize((400, 400))  # Redimensionner pour l'affichage
        img = ImageTk.PhotoImage(image)

        img_label = tk.Label(tab, image=img)
        img_label.image = img  # Garde une référence
        img_label.pack()

        return img_path, img_label
    return None, None

# Fonction pour fermer l'onglet actif
def close_current_tab(tab_control):
    current_tab = tab_control.select()
    if current_tab:
        tab_control.forget(current_tab)

# Application principale
def main():
    root = tk.Tk()
    root.title("Detection de la Langue des Signes")
    root.geometry("600x500")

    tab_control = ttk.Notebook(root)
    tab_control.pack(expand=1, fill="both")

    modele_path = 'bestASL.pt'  # Chemin du modèle YOLO
    img_path = tk.StringVar()  # Variable pour stocker le chemin de l'image
    img_label = None  # Référence à l'image affichée

    # Fonction pour gérer l'importation d'une image
    def on_import_image():
        nonlocal img_path, img_label
        img_path.set('')  # Réinitialiser le chemin de l'image
        path, label = import_image(tab_control)
        if path:
            img_path.set(path)  # Mettre à jour le chemin de l'image
            img_label = label  # Mettre à jour la référence à l'image affichée

    # Fonction pour centrer les boutons dans la fenêtre
    def center_buttons(frame):
        frame.pack(side=tk.BOTTOM, pady=20)

    # Cadre pour les boutons
    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, pady=20)

    # Bouton Importer
    btn_import = tk.Button(button_frame, text="Importer une image", command=on_import_image)
    btn_import.pack(side=tk.LEFT, padx=10)

    # Bouton Prédire
    btn_predict = tk.Button(button_frame, text="Prédire", command=lambda: start_prediction(img_path.get(), modele_path, img_label, root))
    btn_predict.pack(side=tk.LEFT, padx=10)

    # Bouton Fermer l'onglet
    btn_close_tab = tk.Button(button_frame, text="Fermer l'onglet actif", command=lambda: close_current_tab(tab_control))
    btn_close_tab.pack(side=tk.LEFT, padx=10)

    center_buttons(button_frame)

    root.mainloop()

if __name__ == '__main__':
    main()



