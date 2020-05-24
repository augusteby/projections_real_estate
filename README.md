# projections_real_estate

## Hypothèses:
* Opération d'investissement locatif menée avec IL (Investissement Locatif)
* Bien trouvé hors agence (off-market)
* L'emprunt se fait sur le coût sans les frais de notaire (acquisition + plan + travaux + meubles)
* Changement de locataire chaque année
* Fiscalité LMNP

## Utilisation de **generate_projection.py**:
L'utilisateur définie en premier lieu le prix d'acquisition du bien.

D'autres éléments de context sont aussi à définir:
* la ville (cela impact la taxe foncière notamment)
* les couts additionels pour rendre le bien habitable: plans, travaux, meubles
* les frais de service additionnels: notaire, honoraires, frais de gestion locative, frais de recherche des locataires, cout de l'expert comptable, charges de copropriete
* les assurances: pno, gli, emprunteur
* les amortissements (pour le calcul des charges dans le cadre de la fiscalite LMNP): bien, mobilier, travaux, 

Ensuite les variables suivantes sont définis:
* les apports envisagés
* les taux d'intérêt envisagés
* les taux d'occupation envisagés
* les rendements envisagés
* les années de remboursement de crédits envisagés

Pour chaque combinaison de ces variables, les éléments suivants sont estimés par le script:
* le cash à sortir pour l'acquisition du bien
* le loyer mensuel
* si l'impôt est dû ou non lors des premières années
* les revenus annuels
* les coûts annuels
* le cash flow annuel

Un rapport est crée au format csv et permet à l'utilisateur de voir les combinaisons qui lui permettent de générer le plus de cash flow par exemple.

