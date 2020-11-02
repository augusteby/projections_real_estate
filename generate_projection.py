import pandas as pd
import itertools
import numpy as np
from tqdm import tqdm
import joblib


APPORTS_TAUX = [0.1]
TAUX_OCCUPATION = np.arange(0.7, 0.9, 0.1)
ECART_A_LA_MOYENNE_LOYER = np.arange(-0.1, 0.7, 0.1)
ECART_A_LA_MOYENNE_CHARGES_COPRO = np.arange(-0.3, 0.3, 0.1)
ECART_A_LA_MOYENNE_PRIX_M2_AVANT_TRAVAUX = np.arange(-0.5, 0.3, 0.1)
ANNEES_CREDIT_LIST = [20]
TAUX_INTERET = np.arange(0.015, 0.02, 0.005)
OFF_MARKET = [True, False]
VARIABLES_TO_COMBINE = [APPORTS_TAUX, TAUX_OCCUPATION, ECART_A_LA_MOYENNE_LOYER, ANNEES_CREDIT_LIST,
                        TAUX_INTERET, ECART_A_LA_MOYENNE_PRIX_M2_AVANT_TRAVAUX, ECART_A_LA_MOYENNE_CHARGES_COPRO,
                        OFF_MARKET]

# source taxe fonciere: https://www.tacotax.fr/guides/impots-locaux/taxe-fonciere/methode-de-calcul
TAXE_FONCIERE_TAUX = {'reims':0.2926, 'saint_denis':0.2265, 'paris':0.0837, 'marseille': 0.2402,
                      'strasbourg': 0.2249, 'rennes':0.2576, 'tinqueux': 0.155}

COUT_MEUBLES = 7000
COUT_TRAVAUX = 11000
COUT_PLAN = 2000


FRAIS_NOTAIRE_TAUX = 0.075
FRAIS_RECHERCHE_LOCATAIRE = 0
FRAIS_AGENCE_GESTION_TAUX = 0.05
HONORAIRES_IL_TAUX = 0.084

COUT_EXPERT_COMPTABLE_ANNUEL = 300
# source charges copro: https://www.meilleurecopro.com/charges-de-copropriete/
CHARGES_COPRO_M2_ANNUEL = {'reims': 22}


ASSURANCE_PNO_ANNUEL = 150 # assurance proprietaire non occupant (https://reassurez-moi.fr/guide/assurance-habitation/pno-tarif pour des ordres de grandeur)
ASSURANCE_GLI_ANNUEL_TAUX = 0.035 # assurance garantie loyes impayes (https://reassurez-moi.fr/guide/assurance-loyer-impaye/cout) en pourcentage du loyer annuel
ASSURANCE_EMPRUNTEUR_ANNUEL = 15*12

# Pour des ordres de grandeurs pour les amortissements: https://gerant-immo.com/guide/LMNP-amortissement
TAUX_AMORTISSEMENT_BIEN = 0.03
ANNEES_AMORTISSEMENT_MOBILIER = 5
ANNEES_AMORTISSEMENT_TRAVAUX = 10
AMORTISSEMENT_MOBILIER_ANNUEL = COUT_MEUBLES/ANNEES_AMORTISSEMENT_MOBILIER
AMORTISSEMENT_TRAVAUX_ANNUEL = COUT_TRAVAUX/ANNEES_AMORTISSEMENT_TRAVAUX


def get_projection_report(ville, superficie_bien_m2, prix_m2_moyen_zone=None, loyer_m2_moyen_zone=None):
    """
    Quelques hypotheses:
    * Regime LMNP reel
    * Pour simplifier, on ne s'interesse qu'a la premiere annee pour l'impot LMNP
        (on fait l'hypothese que les 5-15 annees suivantes
        donneront le meme resultat: imposable ou pas imposable)
    * On n'inclut pas les cout des meubles et le cout des travaux dans le cout du bien
    """
    TOUTES_COMBINAISONS = list(itertools.product(*VARIABLES_TO_COMBINE))


    projection_dic = {'cout_operation': [],'off_market': [],'rendement_brut': [], 'apport_banque_taux': [],
                      'taux_interet': [], 'annees_emprunt': [],'loyer_mensuel': [],
                      'ecart_au_loyer_moyen': [],
                      'cash_flow_annuel': [], 'cash_flow_annuel_apport_total_inclu': [],'doit_payer_impot': [],
                      'loyer_annuel_percu': [], 'charges_annuel': [], 'taux_occupation': [],
                      'apport_total': [],
                      'ecart_prix_m2_prix_moyen_avant': [], 'ecart_prix_m2_prix_moyen_apres': [],
                      'prix_m2_avant': [], 'prix_m2_apres': [], 'ecart_aux_charges_copro_moyen': [],
                      'first_year_imposition': []}



    for combinaison in tqdm(TOUTES_COMBINAISONS):
        doit_payer_impot = False

        apport_taux_i = combinaison[0]
        taux_occupation_i = combinaison[1]
        ecart_au_loyer_moyen = combinaison[2]
        annees_credit = combinaison[3]
        taux_interet = combinaison[4]
        ecart_prix_m2_prix_moyen_avant = combinaison[5]
        ecart_aux_charges_copro_moyen = combinaison[6]
        off_market = combinaison[7]

        prix_m2_avant = (1 + ecart_prix_m2_prix_moyen_avant) * prix_m2_moyen_zone
        cout_bien = prix_m2_avant * superficie_bien_m2

        frais_notaire = cout_bien * FRAIS_NOTAIRE_TAUX
        amortissement_bien_annuel = TAUX_AMORTISSEMENT_BIEN * cout_bien
        amortissements_hors_bien = AMORTISSEMENT_MOBILIER_ANNUEL + AMORTISSEMENT_TRAVAUX_ANNUEL

        montant_empruntable = cout_bien + COUT_TRAVAUX + COUT_PLAN
        cout_sans_notaire = montant_empruntable + COUT_MEUBLES
        cout_avant_honoraires = cout_sans_notaire + frais_notaire
        if off_market:
            honoraires_il = 0
        else:
            honoraires_il = HONORAIRES_IL_TAUX * cout_avant_honoraires

        cout_operation = cout_avant_honoraires + honoraires_il

        prix_m2_apres = cout_sans_notaire / superficie_bien_m2
        ecart_prix_m2_prix_moyen_apres = (prix_m2_apres - prix_m2_moyen_zone) / prix_m2_moyen_zone

        apport_banque = apport_taux_i * montant_empruntable
        apport_total = COUT_MEUBLES + frais_notaire + apport_banque + honoraires_il

        # Calcul de mortgage
        montant_emprunt = montant_empruntable - apport_banque
        interet = taux_interet * montant_emprunt
        credit = montant_emprunt + interet
        remboursement_annuel_credit = credit / annees_credit

        # Calcul des revenus locatifs annuels a partir du rendement brut vise
        # et en prenant en compte le taux d'occupation
        loyer_mensuel = (1 + ecart_au_loyer_moyen) * loyer_m2_moyen_zone * superficie_bien_m2
        loyer_annuel_theorique = loyer_mensuel * 12
        loyer_annuel_percu = loyer_annuel_theorique * taux_occupation_i
        rendement_brut = loyer_annuel_theorique / cout_operation

        frais_gestion_annuel = FRAIS_AGENCE_GESTION_TAUX * loyer_annuel_theorique

        # Calcul de la taxe fonciere selon:
        # https://www.tacotax.fr/guides/impots-locaux/taxe-fonciere/methode-de-calcul
        # On applique la taxe fonciere definie pour la commune a 50% de la totalite
        # du loyer annuel theorique car il s'agit ici d'une propriete batie
        taxe_fonciere = TAXE_FONCIERE_TAUX[ville] * loyer_annuel_theorique / 2

        assurance_gli_annuelle = ASSURANCE_GLI_ANNUEL_TAUX*loyer_annuel_theorique
        cout_assurances_annuel = ASSURANCE_PNO_ANNUEL + assurance_gli_annuelle + ASSURANCE_EMPRUNTEUR_ANNUEL

        charges_copro_annuel = (1 + ecart_aux_charges_copro_moyen) * CHARGES_COPRO_M2_ANNUEL[ville] * superficie_bien_m2
        depenses_annuelles_gestion_bien = (charges_copro_annuel + frais_gestion_annuel + COUT_EXPERT_COMPTABLE_ANNUEL
                                           + cout_assurances_annuel + FRAIS_RECHERCHE_LOCATAIRE)

        charges_annuel_avant_remboursement_credit = depenses_annuelles_gestion_bien + taxe_fonciere
        charges_annuel = charges_annuel_avant_remboursement_credit + remboursement_annuel_credit

        first_year_of_imposition, compta_par_an = get_fiscalite_lmnp_par_an(annees_credit, loyer_annuel_percu,
                                                                            amortissement_bien_annuel,
                                                                            amortissements_hors_bien,
                                                                            charges_annuel_avant_remboursement_credit,
                                                                            frais_notaire, interet)

        # Pour les couts annuels, on ajoute les frais de notaire et l'apport ammortis sur la duree
        # du pret
        couts_annuel_total = charges_annuel + apport_total / annees_credit

        # On ne s'interesse qu'a la premiere annee. Pour simplifier, on fait l'hypothese que
        # la valeur de la variable doit_payer_impot restera la meme pour de nombreuses annees ensuite
        if first_year_of_imposition == 1:
            doit_payer_impot = True
            #TODO generer la projection dans le cas ou l'impot est dû
        else:
            cash_flow = loyer_annuel_percu - charges_annuel
            cash_flow_total = loyer_annuel_percu - couts_annuel_total

            projection_dic['cout_operation'].append(cout_operation)
            projection_dic['off_market'].append(off_market)
            projection_dic['rendement_brut'].append(rendement_brut)
            projection_dic['apport_banque_taux'].append(apport_taux_i)
            projection_dic['taux_interet'].append(taux_interet)
            projection_dic['annees_emprunt'].append(annees_credit)
            projection_dic['loyer_mensuel'].append(loyer_mensuel)
            projection_dic['ecart_au_loyer_moyen'].append(ecart_au_loyer_moyen)
            projection_dic['cash_flow_annuel'].append(cash_flow)
            projection_dic['cash_flow_annuel_apport_total_inclu'].append(cash_flow_total)
            projection_dic['doit_payer_impot'].append(doit_payer_impot)
            projection_dic['loyer_annuel_percu'].append(loyer_annuel_percu)
            projection_dic['charges_annuel'].append(charges_annuel)
            projection_dic['taux_occupation'].append(taux_occupation_i)
            projection_dic['apport_total'].append(apport_total)
            projection_dic['ecart_prix_m2_prix_moyen_avant'].append(ecart_prix_m2_prix_moyen_avant)
            projection_dic['ecart_prix_m2_prix_moyen_apres'].append(ecart_prix_m2_prix_moyen_apres)
            projection_dic['prix_m2_avant'].append(prix_m2_avant)
            projection_dic['prix_m2_apres'].append(prix_m2_apres)
            projection_dic['ecart_aux_charges_copro_moyen'].append(ecart_aux_charges_copro_moyen)
            projection_dic['first_year_imposition'].append(first_year_of_imposition)

    projection_df = pd.DataFrame(projection_dic)

    return projection_df, compta_par_an

def get_fiscalite_lmnp_par_an(annees_credit, loyer_annuel_percu, amortissement_bien_annuel, amortissements_hors_bien,
                              charges_annuel_avant_remboursement_credit, frais_notaire, interet):
    """
    Sources:
    https://www.smartloc.fr/blog/fiscalite-de-location-meublee-regime-reel-en-lmnp/

    https://www.legifrance.gouv.fr/codes/id/LEGIARTI000006302900/2008-05-01/

    Quelques regles:
    * L'amortissement du bien ne peut creer un deficit ou l'augmenter si il existe deja suite aux imputations des
        depenses reelles (charges directes ou travaux amortis)
    * Il est possible de creer un deficit a partir des seules depenses reelles
    * Un deficit sur une annee (qui ne peut etre cree que par des depenses reelles) peut etre reporte sur les exercices
        suivants dans la limite de 10 ans
    * La part non utilisee de l'amortissement du bien peut etre reporte indefiniment

    Args:
        annees_credit:
        loyer_annuel_percu:
        amortissement_bien_annuel:
        amortissements_hors_bien:
        charges_annuel_avant_remboursement_credit:
        frais_notaire:
        interet:


    Returns:

    """
    compta_par_an = {}

    first_year_of_imposition = 0

    report = 0
    deficit_memory = {'deficit_restant_amort_bien': 0}

    for i in range(1, annees_credit+1):
        compta_annee_i = {}

        compta_annee_i['loyers'] = loyer_annuel_percu

        # La premiere annee, on peut ajouter les frais de notaire aux charges
        # TODO confirmer que l'on puisse aussi ajouter la totalite des interets aux charges la premiere annee
        if i == 1:
            charges_avant_amort_bien =  (amortissements_hors_bien + charges_annuel_avant_remboursement_credit
                                         + frais_notaire + interet)
        else:
            charges_avant_amort_bien = (amortissements_hors_bien + charges_annuel_avant_remboursement_credit
                                        + report)
            report = 0

        charges_apres_amort_bien = charges_avant_amort_bien + amortissement_bien_annuel

        revenus_imposables_avant_amort_bien = loyer_annuel_percu - charges_avant_amort_bien

        revenus_imposables_apres_amort_bien = loyer_annuel_percu - charges_apres_amort_bien

        # si il existe deja un deficit avant la prise en compte de l'amortissement du bien, ou si la prise en compte
        # de l'amortissement du bien engendre un deficit, alors on reporte l'amortissement du bien a l'annee d'apres
        if revenus_imposables_avant_amort_bien < 0 or revenus_imposables_apres_amort_bien < 0:
            deficit_depenses_reelles = np.abs(revenus_imposables_avant_amort_bien)
            report += amortissement_bien_annuel + deficit_avant_amort
            compta_annee_i['charges_totales'] = charges_avant_amort_bien
            compta_annee_i['revenus_imposables'] = revenus_imposables_avant_amort_bien
            compta_annee_i['amort_bien_reporte'] = True
            compta_annee_i['imposable'] = False
            compta_annee_i['report'] = report
            deficit_memory[i] = {'deficit_restant_depenses_reelles': deficit_depenses_reelles,
                                 'annees_restants': 10}
            deficit_memory['deficit_restant_amort_bien'] += amortissement_bien_annuel
        else:
            if first_year_of_imposition == 0:
                first_year_of_imposition = i
            compta_annee_i['charges_totales'] = charges_apres_amort_bien
            compta_annee_i['revenus_imposables'] = revenus_imposables_apres_amort_bien
            compta_annee_i['amort_bien_reporte'] = False
            compta_annee_i['imposable'] = True
            compta_annee_i['report'] = report

        compta_par_an[i] = compta_annee_i

    return first_year_of_imposition, compta_par_an


if __name__=='__main__':
    ville = 'reims'
    superficie_bien_m2 = 50
    prix_m2_moyen_zone = 2300
    loyer_m2_moyen_zone = 9.8

    projection_df, compta_par_an = get_projection_report(ville, superficie_bien_m2, prix_m2_moyen_zone, loyer_m2_moyen_zone)
    projection_df_cash_flow_pos = projection_df[projection_df['cash_flow_annuel']>=0]
    print(projection_df_cash_flow_pos)

    projection_df.to_csv('projection_report_all.csv', index=False)
    projection_df_cash_flow_pos.to_csv('projection_report_cash_flow_pos.csv', index=False)
    print('Rapport de projection genere pour un bien à {} avec une superficie de {} m2'
          ' dans une zone ou le prix au m2 moyen est de {} euros et le loyer au m2 '
          'moyen est de {} euros'.format(ville, superficie_bien_m2, prix_m2_moyen_zone, loyer_m2_moyen_zone))

    fiscalite_lmnp_df = pd.DataFrame(compta_par_an)
    print('')
    print('')
    print(fiscalite_lmnp_df)
    fiscalite_lmnp_df.to_csv('fiscalite_lmnp.csv')
