import pandas as pd
import itertools


APPORTS_PERC = [0.1, 0.15, 0.20, 0.25]
TAUX_OCCUPATION = [1, 0.75, 0.5]
RENDEMENT_BRUT_PERC = [0.035, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07]
ANNEES_CREDIT_LIST = [20, 25]
VARIABLES_TO_COMBINE = [APPORTS_PERC, TAUX_OCCUPATION, RENDEMENT_BRUT_PERC, ANNEES_CREDIT_LIST]

TAUX_INTERET = 0.016

VILLE = 'saint_denis'
# source taxe fonciere: https://www.tacotax.fr/guides/impots-locaux/taxe-fonciere/methode-de-calcul
TAXE_FONCIERE_PERC = {'reims':0.2926, 'saint_denis':0.2265, 'paris':0.0837, 'marseille': 0.2402,
                      'strasbourg': 0.2249, 'rennes':0.2576}

# source: https://www.meilleursagents.com/prix-immobilier/
# TODO: frequently udpate this
PRIX_MOYEN_APPART_M2 = {'reims': 2055, 'saint_denis': 3702, 'aubervilliers': 3784}

COUT_MEUBLES = 7000
COUT_TRAVAUX = 15000
COUT_PLAN = 2000


FRAIS_NOTAIRE_PERC = 0.084
FRAIS_RECHERCHE_LOCATAIRE = 0
FRAIS_AGENCE_GESTION_PERC = 0.06
HONORAIRES_IL_PERC = 0.084

COUT_EXPERT_COMPTABLE_ANNUEL = 300
CHARGES_COPROPRIETE_ANNUEL = 136.8


ASSURANCE_PNO_ANNUEL = 150 # assurance proprietaire non occupant (https://reassurez-moi.fr/guide/assurance-habitation/pno-tarif pour des ordres de grandeur)
ASSURANCE_GLI_ANNUEL = 0 # assurance garantie loyes impayes
ASSURANCE_EMPRUNTEUR_ANNUEL = 0
COUT_ASSURANCES_ANNUEL = ASSURANCE_PNO_ANNUEL + ASSURANCE_GLI_ANNUEL + ASSURANCE_EMPRUNTEUR_ANNUEL

# Pour des ordres de grandeurs pour les amortissements: https://gerant-immo.com/guide/LMNP-amortissement
ANNEES_AMORTISSEMENT_BIEN = 20
ANNEES_AMORTISSEMENT_MOBILIER = 5
ANNEES_AMORTISSEMENT_TRAVAUX = 10
AMORTISSEMENT_MOBILIER_ANNUEL = COUT_MEUBLES/ANNEES_AMORTISSEMENT_MOBILIER
AMORTISSEMENT_TRAVAUX_ANNUEL = COUT_TRAVAUX/ANNEES_AMORTISSEMENT_TRAVAUX


def get_projection_report(cout_bien, superficie_bien_m2):
    """
    Quelques hypotheses:
    * Regime LMNP reel
    * Pour simplifier, on ne s'interesse qu'a la premiere annee pour l'impot LMNP
        (on fait l'hypothese que les 5-15 annees suivantes
        donneront le meme resultat: imposable ou pas imposable)
    * On n'inclut pas les cout des meubles et le cout des travaux dans le cout du bien
    """
    TOUTES_COMBINAISONS = list(itertools.product(*VARIABLES_TO_COMBINE))

    frais_notaire = cout_bien * FRAIS_NOTAIRE_PERC

    amortissement_bien_annuel = cout_bien/ANNEES_AMORTISSEMENT_BIEN

    amortissements = amortissement_bien_annuel + AMORTISSEMENT_MOBILIER_ANNUEL + AMORTISSEMENT_TRAVAUX_ANNUEL

    projection_dic = {'rendement': [], 'apport_perc': [], 'loyer_mensuel': [],
                      'cash_flow_annuel': [], 'doit_payer_impot': [],
                      'revenus_annuel': [], 'couts_annuel': [], 'taux_occupation': [],
                      'cash_a_sortir': [],
                      'ecart_prix_m2_prix_moyen_avant': [], 'ecart_prix_m2_prix_moyen_apres': []}

    cout_sans_notaire = cout_bien + COUT_MEUBLES + COUT_TRAVAUX + COUT_PLAN
    cout_avant_honoraires = cout_sans_notaire + frais_notaire
    honoraires_il = HONORAIRES_IL_PERC * cout_avant_honoraires
    cout_operation = cout_avant_honoraires + honoraires_il

    prix_m2_avant = cout_bien/superficie_bien_m2
    prix_m2_apres = cout_sans_notaire/superficie_bien_m2
    prix_moyen_m2 = PRIX_MOYEN_APPART_M2[VILLE]
    ecart_prix_m2_prix_moyen_avant = 100*(prix_m2_avant-prix_moyen_m2)/prix_moyen_m2
    ecart_prix_m2_prix_moyen_apres = 100*(prix_m2_apres-prix_moyen_m2)/prix_moyen_m2

    for combinaison in TOUTES_COMBINAISONS:
        doit_payer_impot = False

        apport_perc_i = combinaison[0]
        taux_occupation_i = combinaison[1]
        rendement_i = combinaison[2]
        annees_credit = combinaison[3]
        apport = apport_perc_i * cout_sans_notaire

        cash_a_sortir = frais_notaire + apport + honoraires_il

        # Calcul de mortgage
        montant_emprunt = cout_sans_notaire - apport
        interet = TAUX_INTERET * montant_emprunt
        credit = montant_emprunt + interet
        remboursement_annuel_credit = credit / annees_credit

        # Calcul des revenus locatifs annuels a partir du rendement brut vise
        # et en prenant en compte le taux d'occupation
        loyer_annuel = taux_occupation_i * cout_operation * rendement_i
        loyer_mensuel = loyer_annuel / 12

        frais_gestion_annuel = FRAIS_AGENCE_GESTION_PERC * loyer_annuel

        # Calcul de la taxe fonciere selon:
        # https://www.tacotax.fr/guides/impots-locaux/taxe-fonciere/methode-de-calcul
        # On applique la taxe fonciere definie pour la commune a 50% de la totalite
        # du loyer annuel car il s'agit ici d'une propriete batie
        taxe_fonciere = TAXE_FONCIERE_PERC[VILLE] * loyer_annuel / 2

        depenses_annuelles_gestion_bien = (CHARGES_COPROPRIETE_ANNUEL + frais_gestion_annuel
                                           + taxe_fonciere + COUT_EXPERT_COMPTABLE_ANNUEL
                                           + COUT_ASSURANCES_ANNUEL + FRAIS_RECHERCHE_LOCATAIRE)

        # Calcul des charges annuel pour la fiscalite LMNP
        charges_annuel_LMNP = depenses_annuelles_gestion_bien + amortissements

        # La premiere annee, on peut ajouter les frais de notaire aux charges
        # TODO confirmer que l'on puisse aussi ajouter la totalite des interets aux charges la premiere annee
        charges_annuel_LMNP_premiere_annee = charges_annuel_LMNP + frais_notaire + interet

        montant_imposable_LMNP = loyer_annuel - charges_annuel_LMNP
        montant_imposable_LMNP_premiere_annee = loyer_annuel - charges_annuel_LMNP_premiere_annee

        # Pour les couts annuels, on ajoute les frais de notaire et l'apport ammortis sur la duree
        # du pret
        couts_annuel = (depenses_annuelles_gestion_bien + remboursement_annuel_credit
                        + frais_notaire / annees_credit + apport / annees_credit)

        # On ne s'interesse qu'a la premiere annee. Pour simplifier, on fait l'hypothese que
        # la valeur de la variable doit_payer_impot restera la meme pour de nombreuses annees ensuite
        if montant_imposable_LMNP_premiere_annee > 0:
            doit_payer_impot = True
            #TODO generer la projection dans le cas ou l'impot est du
        else:
            cash_flow = loyer_annuel - couts_annuel

            projection_dic['rendement'].append(rendement_i)
            projection_dic['apport_perc'].append(apport_perc_i)
            projection_dic['loyer_mensuel'].append(loyer_mensuel)
            projection_dic['cash_flow_annuel'].append(cash_flow)
            projection_dic['doit_payer_impot'].append(doit_payer_impot)
            projection_dic['revenus_annuel'].append(loyer_annuel)
            projection_dic['couts_annuel'].append(couts_annuel)
            projection_dic['taux_occupation'].append(taux_occupation_i)
            projection_dic['cash_a_sortir'].append(cash_a_sortir)
            projection_dic['ecart_prix_m2_prix_moyen_avant'].append(ecart_prix_m2_prix_moyen_avant)
            projection_dic['ecart_prix_m2_prix_moyen_apres'].append(ecart_prix_m2_prix_moyen_apres)

    projection_df = pd.DataFrame(projection_dic)

    return projection_df


if __name__=='__main__':
    cout_du_bien = 120000
    superficie_bien_m2 = 40

    projection_df = get_projection_report(cout_du_bien, superficie_bien_m2)
    print(projection_df[projection_df['cash_flow_annuel']>=0])

    projection_df.to_csv('projection_report.csv', index=False)
    print('Rapport de projection genere pour un bien de {} euros'.format(cout_du_bien))
