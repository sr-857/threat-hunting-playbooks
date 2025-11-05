rule <Rule_Name>
{
    meta:
        description = "<Short description of the detection>"
        author = "<Author Name>"
        reference = "https://attack.mitre.org/techniques/<TechniqueID>"
        date = "<YYYY-MM-DD>"
        hash = "<Optional sample hash>"

    strings:
        $a = "<pattern or byte sequence>"
        // Add additional strings as needed

    condition:
        $a
}

// Usage Guidance:
// - Replace placeholders in meta and strings sections.
// - Prefer wide and nocase modifiers when relevant.
// - Use Boolean logic in the condition to combine multiple indicators.
