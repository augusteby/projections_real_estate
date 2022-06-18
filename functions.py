import pandas as pd
import numpy as np


def generate_echeancier(montant_emprunt, taux_emprunt_mensuel, annees_credit):
    facteur_comp_taux_mensuel = pow(1 + taux_emprunt_mensuel, annees_credit * 12)
    remboursement_mensuel_credit = (montant_emprunt * taux_emprunt_mensuel * facteur_comp_taux_mensuel) / (
                facteur_comp_taux_mensuel - 1)

    # generation de l'echeancier
    echeancier_dict = {"Mois": [], "Mensualités": [], "Interêts": [], "Capital amorti": [], "Reste dû": []}

    reste_du = montant_emprunt
    for mois in range(1, annees_credit * 12 + 1):
        interet_mois = reste_du * taux_emprunt_mensuel
        capital_amorti_mois = remboursement_mensuel_credit - interet_mois
        reste_du = reste_du - capital_amorti_mois

        echeancier_dict["Mois"].append(mois)
        echeancier_dict["Mensualités"].append(remboursement_mensuel_credit)
        echeancier_dict["Interêts"].append(interet_mois)
        echeancier_dict["Capital amorti"].append(capital_amorti_mois)
        echeancier_dict["Reste dû"].append(reste_du)

    # calculer cumul
    echeancier_dict["Mois"].append(mois)
    echeancier_dict["Mensualités"].append(np.sum(echeancier_dict["Mensualités"]))
    echeancier_dict["Interêts"].append(np.sum(echeancier_dict["Interêts"]))
    echeancier_dict["Capital amorti"].append(np.sum(echeancier_dict["Capital amorti"]))
    echeancier_dict["Reste dû"].append(reste_du)

    echeancier_df = pd.DataFrame(echeancier_dict)

    return echeancier_df, remboursement_mensuel_credit


def generate_fiscalite_lmnp_par_an(loyer_annuel, annees_credit, frais_notaire,
                                   charges_annuel_avant_remboursement_credit,
                                   amortissement_bien_annuel, amortissements_hors_bien, echeancier_df):
    # imposition LMNP micro BIC
    loyers_imposables_micro_bic = 0.5 * loyer_annuel

    # imposition LMNP réel
    loyers_imposables_par_an = {"Année": [], "Loyers imposables micro-BIC": [],
                                "Loyers imposables en réel": []}

    report = 0

    for annee in range(1, annees_credit + 1):
        interets_annee_n = get_interet_annee_n(echeancier_df, n=annee)
        charges_base = charges_annuel_avant_remboursement_credit + amortissements_hors_bien
        if annee == 1:
            charges_avant_amort_bien = charges_base + frais_notaire + interets_annee_n
        else:
            charges_avant_amort_bien = charges_base + interets_annee_n + report

            report = 0

        charges_apres_amort_bien = charges_avant_amort_bien + amortissement_bien_annuel

        loyers_imposables_reel_avant_amort_bien = loyer_annuel - charges_avant_amort_bien

        loyers_imposables_reel_apres_amort_bien = loyer_annuel - charges_apres_amort_bien

        # si il existe deja un deficit avant la prise en compte de l'amortissement du bien, ou si la prise en compte
        # de l'amortissement du bien engendre un deficit, alors on reporte l'amortissement du bien a l'annee d'apres
        if loyers_imposables_reel_avant_amort_bien < 0 or loyers_imposables_reel_apres_amort_bien < 0:
            report += amortissement_bien_annuel

        loyers_imposables_par_an["Année"].append(annee)
        loyers_imposables_par_an["Loyers imposables micro-BIC"].append(loyers_imposables_micro_bic)
        loyers_imposables_par_an["Loyers imposables en réel"].append(loyers_imposables_reel_apres_amort_bien)

    loyers_imposables_par_an_df = pd.DataFrame(loyers_imposables_par_an)

    return loyers_imposables_par_an_df


def get_interet_annee_n(echeancier_df, n=1):
    mois_concernes = list(range(12 * (n - 1) + 1, 12 * n + 1))

    echeancier_df_selec = echeancier_df[echeancier_df["Mois"].isin(mois_concernes)]
    interets_annee_n = echeancier_df_selec["Interêts"].sum()

    return interets_annee_n







