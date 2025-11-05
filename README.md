# Threat Hunting Playbooks

Threat Hunting Playbooks is a curated collection of Sigma and YARA driven hunts paired with enrichment notebooks that document investigation workflows for common attacker behaviors.

## Repository Structure

```
Threat Hunting Playbooks/
├── config/                  # Shared configuration (e.g., data source mappings, tool settings)
├── docs/                    # Project documentation and references
├── hunts/                   # Playbook narratives that tie rules, context, and enrichment steps together
├── notebooks/
│   ├── enrichment/          # Ready-to-run notebooks for enrichment workflows
│   └── templates/           # Notebook templates to standardize new enrichment workflows
├── rules/
│   ├── sigma/
│   │   ├── cloud/
│   │   ├── linux/
│   │   ├── templates/       # Base Sigma templates and helper content
│   │   └── windows/
│   └── yara/
│       ├── linux/
│       ├── templates/       # Base YARA templates and helper content
│       └── windows/
├── scripts/                 # Validation tooling for rules and notebooks
└── requirements.txt         # Python dependencies for notebooks and tooling
```

## Getting Started

1. **Create a virtual environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3. **Launch Jupyter Lab for enrichment notebooks**
    ```bash
    jupyter lab
    ```

## Validation Tooling

- `./scripts/validate_sigma.sh`: Lints Sigma rules and ensures they convert with `sigma-cli`.
- `./scripts/validate_yara.sh`: Compiles YARA rules with `yarac` to catch syntax errors.

Run the scripts from the repository root after adding or modifying rules:

```bash
./scripts/validate_sigma.sh
./scripts/validate_yara.sh
```

## Authoring a New Hunt

1. **Identify attacker behavior**: Map the behavior to MITRE ATT&CK tactics and techniques.
2. **Create or adapt detection rules**:
   - Use the Sigma template in `rules/sigma/templates` to build detections.
   - Use the YARA template in `rules/yara/templates` when binary or memory scanning is needed.
3. **Document enrichment workflow**: Copy the enrichment notebook template, implement data pulls, enrichment steps, and investigative guidance.
4. **Write the hunt narrative**: Document assumptions, prerequisites, detection logic, enrichment steps, and response guidance under `hunts/`.
5. **Update documentation**: Add references, tuning notes, and validation steps in `docs/` as necessary.

## Contributing

-- Follow the templates provided for rules, notebooks, and hunt narratives to maintain consistency.
- Use the validation scripts in `scripts/` to lint Sigma and YARA artifacts before submission.
- Include ATT&CK mappings, references, and testing notes in every hunt.

## Roadmap

- Expand cloud-centric Sigma detections (AWS, Azure, GCP).
- Add automated validation pipelines for rule linting and notebook execution.
- Integrate threat intelligence enrichment (VirusTotal, MISP, etc.).

## License

Specify licensing terms in `LICENSE` (to be added).
