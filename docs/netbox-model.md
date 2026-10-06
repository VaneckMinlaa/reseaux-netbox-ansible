# Modèle de données NetBox

Tout ce qui influence la config générée doit vivre ici (ou dans Vault pour les secrets).

## Objets obligatoires

| Objet | Exemple | Usage template |
|-------|---------|----------------|
| Site | `pilote`, `prod-sim` | filtre déploiement, banner |
| Platform | `cisco_ios`, `arista_eos` | choix du fichier Jinja2 |
| Device role | `access`, `distribution` | banner / STP |
| Device | `SW-PILOTE-01` | hostname |
| Primary IP | `10.10.10.11/24` | `ansible_host`, VLAN mgmt |
| VLAN (par site) | 10 USERS, 20 VOICE | section `vlan` |
| Interface | mode access/trunk, VLAN, description | `switchport ...` |

## Custom fields recommandés (Device)

| Name | Type | Exemple |
|------|------|---------|
| `mgmt_mask` | Text | `255.255.255.0` |
| `default_gateway` | Text | `10.10.10.1` |
| `domain_name` | Text | `lab.local` |
| `ntp_servers` | Text (CSV) ou JSON | `10.0.0.1,10.0.0.2` |
| `snmp_location` | Text | `Batiment A` |
| `stp_priority` | Integer | `24576` |

Secrets (`enable secret`, SNMP community, users) → **Ansible Vault** / variables CI, pas NetBox en clair.

## Platforms (slugs)

Utiliser exactement :

- `cisco_ios`
- `arista_eos`

Le moteur mappe vers `templates/<platform>/base.j2`.

## Interfaces

- Access : `802.1Q` mode Access + Untagged VLAN  
- Trunk : mode Tagged + Tagged VLANs = allowed list  

## Checklist peuplement lab

1. Sites `pilote` + `prod-sim`  
2. Platforms + roles  
3. VLANs par site  
4. Devices + primary IP  
5. Interfaces uplink en trunk  
6. Custom fields remplis  
7. `SOURCE_MODE=netbox` + test `python scripts/cli.py generate --site pilote`
