# Runbook opérationnel

## Déployer un changement de politique

1. Modifier NetBox (ou `data/demo_devices.yaml` en lab)  
2. `python scripts/cli.py generate`  
3. `python scripts/cli.py validate`  
4. Review du diff Git sur `configs/expected/` (optionnel : commit des configs générées)  
5. CI : job **deploy_pilot** (manuel)  
6. Tests pilote  
7. CI : job **deploy_prod** (manuel)

## Traiter une alerte de dérive

1. Ouvrir l’artifact `reports/drift_*.md`  
2. Classifier :
   - **Légitime** → reporter le changement dans NetBox, régénérer, redéployer  
   - **Non autorisé** → `ansible-playbook playbooks/deploy.yml --limit <host>` pour réaligner  
3. Relancer `python scripts/cli.py drift` pour confirmer OK  

## Ajouter un vendor

1. Créer `templates/<platform_slug>/base.j2`  
2. Ajouter le mapping dans `netops/render.py` → `PLATFORM_TEMPLATE`  
3. Ajouter `group_vars/<platform>.yml` + tâches deploy/collect dans les playbooks  
4. Créer la Platform dans NetBox avec le même slug  

## Ajouter un site

1. Site NetBox + VLANs + devices  
2. Groupe inventaire Ansible (`site_<slug>`)  
3. Premier deploy avec `--limit` explicite
