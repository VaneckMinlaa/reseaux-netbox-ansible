# Lab PNETLab recommandé

## Topologie minimale

```
              [ mgmt cloud / LAN ]
                      |
              +-------+-------+
              |               |
        SW-PILOTE-01    SW-PILOTE-02
         (Cisco IOS)     (Arista EOS*)
              |               |
              +-------+-------+
                      |
                 (optionnel)
                 SW-PROD-01
                 (Cisco IOS)
```

\* Si tu n’as pas d’image Arista, duplique un second Cisco et change seulement le hostname / site dans `data/demo_devices.yaml` et l’inventaire — le template `arista_eos` restera prêt pour plus tard.

## Adressage lab (exemple)

| Équipement | Mgmt IP | Site |
|------------|---------|------|
| Ubuntu NetOps VM | 10.10.10.5 | — |
| SW-PILOTE-01 | 10.10.10.11 | pilote |
| SW-PILOTE-02 | 10.10.10.12 | pilote |
| SW-PROD-01 | 10.20.20.11 | prod-sim |
| Gateway | 10.10.10.1 / 10.20.20.1 | — |

Adapte `inventories/demo/hosts.yml` et `data/demo_devices.yaml` à tes IP réelles.

## Bootstrap SSH sur les switches

Avant le premier deploy automatisé, configure manuellement une IP mgmt + user SSH + enable. Ensuite la vérité revient à NetBox + templates.

## Tests connectivité depuis la VM NetOps

```bash
ping -c 2 10.10.10.11
ssh admin@10.10.10.11
ansible -i inventories/demo/hosts.yml site_pilote -m cisco.ios.ios_command -a "commands='show version'" --limit SW-PILOTE-01
```

## Ordre de déploiement

1. Générer + valider  
2. Deploy **uniquement** `site_pilote`  
3. Vérifier VLANs / trunk / SSH  
4. Deploy `site_prod_sim`
