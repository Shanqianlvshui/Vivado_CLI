from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DOCS_ROOT_ENV = "VIVADO_MCP_DOCS_ROOT"
DEFAULT_LOCAL_DOCS_ROOT = r"C:\Database\FPGA\Vivado_docs"


@dataclass(frozen=True)
class OfficialReference:
    doc_id: str
    title: str
    url: str
    version: str
    release_date: str
    scope: str
    topics: tuple[str, ...]
    use_when: tuple[str, ...]
    local_filenames: tuple[str, ...] = ()

    @property
    def resource_uri(self) -> str:
        return f"vivado://official-docs/{self.doc_id.lower()}"

    def to_dict(self) -> dict[str, object]:
        local_path_candidates = _local_path_candidates(self.local_filenames)
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "url": self.url,
            "version": self.version,
            "release_date": self.release_date,
            "scope": self.scope,
            "topics": list(self.topics),
            "use_when": list(self.use_when),
            "local_filenames": list(self.local_filenames),
            "local_docs_root": local_docs_root(),
            "local_path_candidates": local_path_candidates,
            "available_local_paths": [path for path in local_path_candidates if Path(path).is_file()],
            "resource_uri": self.resource_uri,
        }


OFFICIAL_REFERENCES: tuple[OfficialReference, ...] = (
    OfficialReference(
        doc_id="UG835",
        title="Vivado Design Suite Tcl Command Reference Guide",
        url="https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands",
        version="2025.2 English",
        release_date="2025-11-20",
        scope="Command-level Vivado Tcl reference. Treat this as the first authority for syntax, options, object returns, and examples.",
        topics=("tcl", "commands", "api", "project", "bd", "ip", "constraints", "synthesis", "implementation", "reports", "simulation", "hardware"),
        use_when=(
            "Checking exact syntax for a Vivado Tcl command.",
            "Designing or reviewing an MCP workflow tool that wraps Tcl.",
            "Falling back to expert raw Tcl mode.",
        ),
        local_filenames=("ug835.pdf",),
    ),
    OfficialReference(
        doc_id="UG894",
        title="Vivado Design Suite User Guide: Using Tcl Scripting",
        url="https://docs.amd.com/r/en-US/ug894-vivado-tcl-scripting",
        version="2025.2 English",
        release_date="2025-12-03",
        scope="Tcl scripting methodology, object queries, custom procedures, script loading, error handling, and Tcl Store guidance.",
        topics=("tcl", "scripting", "objects", "queries", "procedures", "gui", "batch", "custom-drc"),
        use_when=(
            "Writing multi-step Tcl scripts instead of single commands.",
            "Querying or filtering Vivado first-class objects.",
            "Deciding how to structure reusable Tcl helpers.",
        ),
        local_filenames=("ug894.pdf",),
    ),
    OfficialReference(
        doc_id="UG892",
        title="Vivado Design Suite User Guide: Design Flows Overview",
        url="https://docs.amd.com/r/en-US/ug892-vivado-design-flows-overview",
        version="2025.2 English",
        release_date="2025-11-20",
        scope="Project Mode, Non-Project Mode, batch Tcl scripts, IDE/Tcl use models, source control, and end-to-end design flow context.",
        topics=("flows", "project", "non-project", "batch", "gui", "tcl", "source-control"),
        use_when=(
            "Choosing between Project Mode and Non-Project Mode.",
            "Explaining how a Tcl flow maps to Vivado run infrastructure.",
            "Planning source-control friendly automation.",
        ),
        local_filenames=("ug892.pdf", "ug892.txt"),
    ),
    OfficialReference(
        doc_id="UG888",
        title="Vivado Design Suite Tutorial: Design Flows Overview",
        url="https://docs.amd.com/r/en-US/ug888-vivado-design-flows-overview-tutorial",
        version="2017.4 English",
        release_date="2017-12-20",
        scope="Tutorial-level walkthroughs for Vivado design flows, useful as concrete examples after choosing the intended flow from UG892.",
        topics=("tutorial", "flows", "project", "non-project", "batch", "tcl", "gui"),
        use_when=(
            "Looking for a concrete project or non-project flow example.",
            "Creating beginner-facing MCP help or smoke-test walkthroughs.",
            "Checking how official tutorials sequence Vivado operations.",
        ),
        local_filenames=("ug888.pdf",),
    ),
    OfficialReference(
        doc_id="UG893",
        title="Vivado Design Suite User Guide: Using the Vivado IDE",
        url="https://docs.amd.com/r/en-US/ug893-vivado-ide",
        version="Latest AMD online reference",
        release_date="See AMD documentation",
        scope="Vivado IDE behavior, Tcl Console usage, GUI project interaction, layout, source views, and GUI-driven flow context.",
        topics=("gui", "ide", "tcl-console", "project", "sources", "runs", "reports"),
        use_when=(
            "Explaining how GUI-visible actions relate to Tcl-driven automation.",
            "Designing MCP help for users watching or interacting with the Vivado IDE.",
            "Checking IDE concepts before mapping them to Tcl commands.",
        ),
        local_filenames=("ug893.pdf",),
    ),
    OfficialReference(
        doc_id="UG895",
        title="Vivado Design Suite User Guide: System-Level Design Entry",
        url="https://docs.amd.com/r/en-US/ug895-vivado-system-level-design-entry",
        version="2025.2 English",
        release_date="2025-11-20",
        scope="Project creation, source management, constraints files, board flow, IP sources, block design sources, and RTL elaboration.",
        topics=("project", "sources", "constraints", "ip", "bd", "board", "rtl", "elaboration", "tcl"),
        use_when=(
            "Adding or organizing RTL, constraints, IP, and BD sources.",
            "Creating or opening projects through Tcl.",
            "Understanding board-flow project setup.",
        ),
        local_filenames=("ug895.pdf",),
    ),
    OfficialReference(
        doc_id="UG912",
        title="Vivado Design Suite Properties Reference Guide",
        url="https://docs.amd.com/r/en-US/ug912-vivado-properties",
        version="2025.2 English",
        release_date="2025-11-20",
        scope="Vivado first-class object properties, applicable object types, accepted values, and HDL/XDC syntax examples.",
        topics=("properties", "set-property", "get-property", "objects", "constraints", "bd", "hardware"),
        use_when=(
            "Setting or reading Vivado object properties.",
            "Checking object-specific property names and values.",
            "Building property-aware summaries for projects, BD designs, and hardware objects.",
        ),
        local_filenames=("ug912.pdf",),
    ),
    OfficialReference(
        doc_id="UG903",
        title="Vivado Design Suite User Guide: Using Constraints",
        url="https://docs.amd.com/r/en-US/ug903-vivado-using-constraints",
        version="2025.2 English",
        release_date="2025-11-20",
        scope="XDC constraints, timing constraints, physical constraints, constraints order, scoping, and supported SDC command behavior.",
        topics=("constraints", "xdc", "timing", "physical", "clocks", "exceptions", "properties"),
        use_when=(
            "Creating or reviewing XDC constraints.",
            "Diagnosing timing-constraint coverage or ordering.",
            "Deciding whether to use read_xdc, source, or constraint sets.",
        ),
        local_filenames=("ug903.pdf",),
    ),
    OfficialReference(
        doc_id="UG994",
        title="Vivado Design Suite User Guide: Designing IP Subsystems Using IP Integrator",
        url="https://docs.amd.com/r/en-US/ug994-vivado-ip-subsystems",
        version="2025.2 English",
        release_date="2025-11-26",
        scope="IP Integrator block designs, BD Tcl scripts, automation, validation, addressing, wrappers, output products, and BD containers.",
        topics=("bd", "block-design", "ip-integrator", "ip", "automation", "addressing", "output-products", "wrapper", "tcl"),
        use_when=(
            "Creating or modifying block designs.",
            "Using Designer Assistance or BD automation.",
            "Generating, exporting, or reusing BD output products and Tcl scripts.",
        ),
        local_filenames=("ug994.pdf",),
    ),
    OfficialReference(
        doc_id="UG896",
        title="Vivado Design Suite User Guide: Designing with IP",
        url="https://docs.amd.com/r/en-US/ug896-vivado-ip",
        version="2025.2 English",
        release_date="2025-12-17",
        scope="IP catalog, IP customization, IP repositories, generated output products, IP simulation, upgrades, and common IP Tcl flows.",
        topics=("ip", "ip-catalog", "xci", "output-products", "upgrade-ip", "simulation", "repository", "tcl"),
        use_when=(
            "Creating, configuring, upgrading, or generating IP.",
            "Managing IP repositories and IP output products.",
            "Adding IP-specific simulation or support files.",
        ),
        local_filenames=("ug896.pdf",),
    ),
    OfficialReference(
        doc_id="UG899",
        title="Vivado Design Suite User Guide: I/O and Clock Planning",
        url="https://docs.amd.com/r/en-US/ug899-vivado-io-clock-planning",
        version="Latest AMD online reference",
        release_date="See AMD documentation",
        scope="I/O planning, package pins, clock resources, pin assignment, board planning, and related constraints/report flows.",
        topics=("io", "clock-planning", "pins", "package", "constraints", "xdc", "reports", "board"),
        use_when=(
            "Planning or reviewing pin assignments and clock-capable I/O usage.",
            "Generating or validating I/O-related constraints.",
            "Diagnosing package, banking, or clock-planning report issues.",
        ),
        local_filenames=("ug899.pdf",),
    ),
    OfficialReference(
        doc_id="UG1118",
        title="Vivado Design Suite User Guide: Creating and Packaging Custom IP",
        url="https://docs.amd.com/r/en-US/ug1118-vivado-creating-packaging-custom-ip",
        version="2025.2 English",
        release_date="2025-12-17",
        scope="Custom IP packaging, bus interface definitions, IP-XACT metadata, packaged BD flows, customization parameters, and encryption.",
        topics=("ip", "custom-ip", "ip-packager", "ip-xact", "bus-interface", "packaging", "bd"),
        use_when=(
            "Packaging RTL or a block design as reusable IP.",
            "Editing bus interfaces or customization parameters.",
            "Adding IP packaging support to MCP workflows.",
        ),
        local_filenames=("ug1118.pdf",),
    ),
    OfficialReference(
        doc_id="UG900",
        title="Vivado Design Suite User Guide: Logic Simulation",
        url="https://docs.amd.com/r/en-US/ug900-vivado-logic-simulation",
        version="2025.2 English",
        release_date="2025-12-17",
        scope="Vivado simulator, third-party simulation integration, simulation libraries, launch_simulation, waveforms, SAIF, VCD, and IP simulation.",
        topics=("simulation", "xsim", "launch-simulation", "compile-simlib", "waveforms", "saif", "vcd", "ip"),
        use_when=(
            "Launching or debugging simulation flows.",
            "Preparing simulation libraries or waveform output.",
            "Adding simulation support to project automation.",
        ),
        local_filenames=("ug900.pdf",),
    ),
    OfficialReference(
        doc_id="UG901",
        title="Vivado Design Suite User Guide: Synthesis",
        url="https://docs.amd.com/r/en-US/ug901-vivado-synthesis",
        version="2025.2 English",
        release_date="2025-12-05",
        scope="Vivado synthesis, synthesis settings, strategies, Tcl synthesis examples, linter, attributes, and HDL coding guidance.",
        topics=("synthesis", "synth-design", "runs", "linter", "attributes", "rtl", "tcl"),
        use_when=(
            "Running or configuring synthesis.",
            "Reviewing synthesis attributes and linter output.",
            "Building synthesis-stage MCP checks.",
        ),
        local_filenames=("ug901.pdf",),
    ),
    OfficialReference(
        doc_id="UG904",
        title="Vivado Design Suite User Guide: Implementation",
        url="https://docs.amd.com/r/en-US/ug904-vivado-implementation",
        version="2025.2 English",
        release_date="2025-11-20",
        scope="Implementation flow, opt/place/phys_opt/route commands, run strategies, checkpoints, incremental compile, and reports.",
        topics=("implementation", "opt-design", "place-design", "phys-opt-design", "route-design", "runs", "checkpoints", "reports", "tcl"),
        use_when=(
            "Running or customizing implementation.",
            "Using implementation steps directly in Non-Project Mode.",
            "Diagnosing run strategies, checkpoints, and incremental compile behavior.",
        ),
        local_filenames=("ug904.pdf",),
    ),
    OfficialReference(
        doc_id="UG906",
        title="Vivado Design Suite User Guide: Design Analysis and Closure Techniques",
        url="https://docs.amd.com/r/en-US/ug906-vivado-design-analysis",
        version="2025.2 English",
        release_date="2025-12-10",
        scope="Timing/utilization/DRC/methodology reports, design analysis, messages, waivers, timing closure, and report interpretation.",
        topics=("reports", "timing", "utilization", "drc", "methodology", "waivers", "closure", "analysis"),
        use_when=(
            "Interpreting reports after synthesis or implementation.",
            "Building report parsers and diagnosis guidance.",
            "Planning timing-closure or methodology checks.",
        ),
        local_filenames=("ug906.pdf",),
    ),
    OfficialReference(
        doc_id="UG907",
        title="Vivado Design Suite User Guide: Power Analysis and Optimization",
        url="https://docs.amd.com/r/en-US/ug907-vivado-power-analysis-optimization",
        version="2025.2 English",
        release_date="2025-11-20",
        scope="Power analysis, report_power, switching activity, SAIF, power optimization, power rails, and Tcl-based power workflows.",
        topics=("power", "report-power", "activity", "saif", "optimization", "reports", "tcl"),
        use_when=(
            "Running or interpreting power analysis.",
            "Using SAIF/VCD activity in power estimation.",
            "Adding power optimization or report_power support.",
        ),
        local_filenames=("ug907.pdf",),
    ),
    OfficialReference(
        doc_id="UG908",
        title="Vivado Design Suite User Guide: Programming and Debugging",
        url="https://docs.amd.com/r/en-US/ug908-vivado-programming-debugging",
        version="2025.2 English",
        release_date="2025-11-20",
        scope="Hardware Manager, hw_server connections, device programming, debug probes, ILA/VIO/IBERT, and programming/debug Tcl flows.",
        topics=("hardware", "debug", "programming", "hw-server", "hardware-manager", "ila", "vio", "ibert", "tcl"),
        use_when=(
            "Designing future hardware-manager MCP support.",
            "Programming devices or connecting hardware targets through Tcl.",
            "Debugging probes, ILAs, VIOs, and hardware sessions.",
        ),
        local_filenames=("ug908.pdf",),
    ),
    OfficialReference(
        doc_id="UG909",
        title="Vivado Design Suite User Guide: Dynamic Function eXchange",
        url="https://docs.amd.com/r/en-US/ug909-vivado-partial-reconfiguration",
        version="2025.2 English",
        release_date="2025-12-17",
        scope="Dynamic Function eXchange flows, reconfigurable partitions/modules, DFX constraints, Tcl scripts, project flow, and partial bitstreams.",
        topics=("dfx", "partial-reconfiguration", "implementation", "bitstream", "constraints", "tcl", "bd"),
        use_when=(
            "Working with Dynamic Function eXchange or partial bitstreams.",
            "Creating or reviewing DFX project Tcl flows.",
            "Handling BD containers used as reconfigurable partitions.",
        ),
        local_filenames=("ug909.pdf",),
    ),
    OfficialReference(
        doc_id="UG911",
        title="ISE to Vivado Design Suite Migration Guide",
        url="https://docs.amd.com/r/en-US/ug911-vivado-migration",
        version="2020.2 English",
        release_date="2020-11-18",
        scope="Migration from ISE flows to Vivado, including constraint conversion, command differences, project structure, and methodology changes.",
        topics=("migration", "ise", "vivado", "constraints", "project", "tcl", "methodology"),
        use_when=(
            "Helping migrate legacy ISE projects or scripts to Vivado.",
            "Explaining command or constraint differences from older flows.",
            "Triaging Tcl scripts that assume ISE behavior.",
        ),
        local_filenames=("ug911.pdf",),
    ),
    OfficialReference(
        doc_id="UG949",
        title="UltraFast Design Methodology Guide for FPGAs and SoCs",
        url="https://docs.amd.com/r/en-US/ug949-vivado-design-methodology",
        version="Latest AMD online reference",
        release_date="See AMD documentation",
        scope="AMD recommended design methodology, constraints methodology, timing closure, implementation strategy, reports, and review checkpoints.",
        topics=("methodology", "ultrafast", "constraints", "timing", "implementation", "closure", "reports", "project"),
        use_when=(
            "Turning Vivado reports into design-closure guidance.",
            "Adding methodology-aware MCP recommendations.",
            "Reviewing constraint, synthesis, and implementation strategy choices.",
        ),
        local_filenames=("ug949.pdf",),
    ),
    OfficialReference(
        doc_id="UG1292",
        title="UltraFast Design Methodology Timing Closure Quick Reference Guide",
        url="https://docs.amd.com/r/en-US/ug1292-ultrafast-timing-closure-quick-reference",
        version="2025.1 English",
        release_date="2025-05-29",
        scope="Timing closure checklist and quick-reference guidance for constraints, implementation, reports, and iterative closure.",
        topics=("timing", "closure", "methodology", "constraints", "implementation", "reports"),
        use_when=(
            "Providing short timing-closure next steps after a failing timing report.",
            "Building checklist-style report diagnosis output.",
            "Prioritizing constraints and implementation fixes.",
        ),
        local_filenames=("ug1292.pdf",),
    ),
    OfficialReference(
        doc_id="UG973",
        title="Vivado Design Suite User Guide: Release Notes, Installation, and Licensing",
        url="https://docs.amd.com/r/en-US/ug973-vivado-release-notes-install-license",
        version="Latest AMD online reference",
        release_date="See AMD documentation",
        scope="Vivado installation, licensing, platform support, release notes, known issues, environment setup, and tool availability.",
        topics=("installation", "licensing", "release-notes", "environment", "platform", "versions"),
        use_when=(
            "Diagnosing installation, licensing, or version issues.",
            "Checking platform support and release-specific caveats.",
            "Explaining why a local Vivado command or feature may not be present.",
        ),
        local_filenames=("ug973.pdf",),
    ),
    OfficialReference(
        doc_id="UG953",
        title="Vivado Design Suite 7 Series FPGA and Zynq-7000 SoC Libraries Guide",
        url="https://docs.amd.com/r/en-US/ug953-vivado-7series-libraries",
        version="2016.4 English",
        release_date="2017-07-24",
        scope="7 Series and Zynq-7000 primitive/library reference for HDL instantiation, attributes, and synthesis-visible device primitives.",
        topics=("libraries", "primitives", "7-series", "zynq-7000", "hdl", "synthesis"),
        use_when=(
            "Checking primitive instantiation syntax for 7 Series or Zynq-7000 designs.",
            "Reviewing HDL that directly instantiates device-specific libraries.",
            "Explaining synthesis behavior tied to library primitives.",
        ),
        local_filenames=("ug953.pdf",),
    ),
    OfficialReference(
        doc_id="UG974",
        title="UltraScale Architecture Libraries Guide",
        url="https://docs.amd.com/r/en-US/ug974-vivado-ultrascale-libraries",
        version="Latest AMD online reference",
        release_date="See AMD documentation",
        scope="UltraScale and UltraScale+ primitive/library reference for HDL instantiation, attributes, and synthesis-visible device primitives.",
        topics=("libraries", "primitives", "ultrascale", "ultrascale-plus", "hdl", "synthesis"),
        use_when=(
            "Checking primitive instantiation syntax for UltraScale or UltraScale+ designs.",
            "Reviewing HDL that directly instantiates architecture libraries.",
            "Explaining synthesis behavior tied to UltraScale library primitives.",
        ),
        local_filenames=("ug974.pdf",),
    ),
    OfficialReference(
        doc_id="UG1046",
        title="UltraFast Embedded Design Methodology Guide",
        url="https://docs.amd.com/r/en-US/ug1046-ultrafast-design-methodology-guide",
        version="Latest AMD online reference",
        release_date="See AMD documentation",
        scope="Embedded system design methodology for AMD SoC/MPSoC devices, including platform, software, hardware, and integration considerations.",
        topics=("embedded", "methodology", "zynq", "mpsoc", "versal", "platform", "hardware", "software"),
        use_when=(
            "Planning embedded-oriented Vivado flows with processors or platforms.",
            "Connecting Vivado hardware design work to software/platform methodology.",
            "Explaining SoC/MPSoC methodology beyond basic programmable logic flows.",
        ),
        local_filenames=("ug1046.pdf",),
    ),
)


TOPIC_GUIDES: dict[str, dict[str, object]] = {
    "tcl": {
        "summary": "Use UG835 for exact command syntax and UG894 for script structure, object querying, and error handling. Use UG893 for Tcl Console/IDE context and the current Vivado process's `help <command>` as the installed-version check.",
        "doc_ids": ("UG835", "UG894", "UG893", "UG892"),
    },
    "project": {
        "summary": "Use UG892 for flow choice, UG895 for project/source operations, UG893 for IDE context, UG835 for command syntax, and UG912 when properties are involved.",
        "doc_ids": ("UG892", "UG895", "UG893", "UG888", "UG835", "UG912"),
    },
    "bd": {
        "summary": "Use UG994 for IP Integrator workflow concepts, UG835 for each BD Tcl command, UG912 for BD object properties, and UG895/UG896 when BD sources or IP output products touch the project.",
        "doc_ids": ("UG994", "UG835", "UG912", "UG895", "UG896", "UG1118"),
    },
    "ip": {
        "summary": "Use UG896 for IP catalog/customization/output products, UG994 for IP Integrator subsystems, UG1118 for packaging custom IP, and UG835 for command syntax.",
        "doc_ids": ("UG896", "UG994", "UG1118", "UG835", "UG912"),
    },
    "constraints": {
        "summary": "Use UG903 for XDC methodology and timing/physical constraints, UG899 for I/O and clock planning constraints, UG912 for property details, and UG835 for command syntax.",
        "doc_ids": ("UG903", "UG899", "UG912", "UG835"),
    },
    "build": {
        "summary": "Use UG901 for synthesis, UG904 for implementation, UG906 for analysis/report interpretation, UG949/UG1292 for methodology and closure, and UG835 for command syntax.",
        "doc_ids": ("UG901", "UG904", "UG906", "UG949", "UG1292", "UG835"),
    },
    "simulation": {
        "summary": "Use UG900 for simulation flows and UG896 when simulation concerns IP output products or IP simulation models.",
        "doc_ids": ("UG900", "UG896", "UG835"),
    },
    "reports": {
        "summary": "Use UG906 for timing/utilization/DRC/methodology interpretation, UG907 for power, UG949/UG1292 for closure guidance, and UG835 for report command syntax.",
        "doc_ids": ("UG906", "UG907", "UG949", "UG1292", "UG835"),
    },
    "hardware": {
        "summary": "Use UG908 for Hardware Manager, programming, hw_server, and debug flows. Hardware actions should stay outside default safe automation until separate safety policy exists.",
        "doc_ids": ("UG908", "UG835", "UG912"),
    },
    "dfx": {
        "summary": "Use UG909 for Dynamic Function eXchange flow rules and UG835/UG912 for Tcl command and property details.",
        "doc_ids": ("UG909", "UG835", "UG912"),
    },
    "methodology": {
        "summary": "Use UG949 as the main methodology guide, UG1292 for timing closure checklists, and the flow-specific guides for exact commands and reports.",
        "doc_ids": ("UG949", "UG1292", "UG906", "UG903", "UG901", "UG904"),
    },
    "io": {
        "summary": "Use UG899 for I/O and clock planning, UG903 for XDC constraints, UG912 for properties, and UG835 for command syntax.",
        "doc_ids": ("UG899", "UG903", "UG912", "UG835"),
    },
    "installation": {
        "summary": "Use UG973 for installation, licensing, platform support, release notes, and version-specific caveats.",
        "doc_ids": ("UG973",),
    },
    "migration": {
        "summary": "Use UG911 for ISE-to-Vivado migration and then verify converted constraints and commands with UG903, UG835, and UG912.",
        "doc_ids": ("UG911", "UG903", "UG835", "UG912"),
    },
    "libraries": {
        "summary": "Use UG953 for 7 Series/Zynq-7000 primitives and UG974 for UltraScale/UltraScale+ primitives.",
        "doc_ids": ("UG953", "UG974", "UG901"),
    },
    "embedded": {
        "summary": "Use UG1046 for embedded methodology and combine it with UG994/UG896/UG908 when platforms, IP subsystems, or hardware debug are involved.",
        "doc_ids": ("UG1046", "UG994", "UG896", "UG908"),
    },
}

TOPIC_ALIASES: dict[str, str] = {
    "block-design": "bd",
    "ipi": "bd",
    "ip-integrator": "bd",
    "project-flow": "project",
    "flow": "project",
    "flows": "project",
    "tutorial": "project",
    "source": "project",
    "sources": "project",
    "xdc": "constraints",
    "constraint": "constraints",
    "pin": "io",
    "pins": "io",
    "io-planning": "io",
    "clock": "io",
    "clock-planning": "io",
    "synthesis": "build",
    "implementation": "build",
    "method": "methodology",
    "ultrafast": "methodology",
    "timing": "reports",
    "power": "reports",
    "closure": "reports",
    "debug": "hardware",
    "programming": "hardware",
    "partial-reconfiguration": "dfx",
    "install": "installation",
    "license": "installation",
    "licensing": "installation",
    "release": "installation",
    "version": "installation",
    "ise": "migration",
    "primitive": "libraries",
    "primitives": "libraries",
    "library": "libraries",
    "soc": "embedded",
    "platform": "embedded",
}


def list_official_references(query: str | None = None, topic: str | None = None) -> list[dict[str, object]]:
    query_terms = _terms(query)
    topic_key = normalize_topic(topic)
    topic_doc_ids = set(TOPIC_GUIDES.get(topic_key or "", {}).get("doc_ids", ()))

    rows = []
    for reference in OFFICIAL_REFERENCES:
        if topic_doc_ids and reference.doc_id not in topic_doc_ids:
            continue
        haystack = _reference_text(reference)
        if query_terms and not all(term in haystack for term in query_terms):
            continue
        rows.append(reference.to_dict())
    return rows


def get_official_reference(doc_id: str) -> dict[str, object]:
    reference = _find_reference(doc_id)
    result = reference.to_dict()
    result["authority_note"] = (
        "This MCP package embeds AMD official documentation metadata and routing guidance, "
        "not the copyrighted document body. Use the AMD URL or a user-provided local PDF for full text."
    )
    return result


def official_reference_guide(topic: str | None = None) -> dict[str, object]:
    topic_key = normalize_topic(topic) or "tcl"
    guide = TOPIC_GUIDES.get(topic_key)
    if guide is None:
        return {
            "topic": topic_key,
            "summary": "Unknown reference topic. Use `vivado_list_official_references` without filters to inspect the packaged AMD documentation catalog.",
            "recommended_order": [],
            "references": [],
            "related_resources": ["vivado://official-docs/index"],
        }

    references = [get_official_reference(doc_id) for doc_id in guide["doc_ids"]]
    return {
        "topic": topic_key,
        "summary": guide["summary"],
        "recommended_order": list(guide["doc_ids"]),
        "references": references,
        "related_resources": ["vivado://official-docs/index", "vivado://skills/official-docs-reference"],
    }


def official_docs_index() -> str:
    lines = [
        "# Vivado Official References",
        "",
        "This MCP package includes AMD official documentation metadata and AI routing guidance for Vivado automation. It does not embed full AMD document text or per-IP product guide bodies.",
        "",
        f"- Local docs root: `{local_docs_root()}`",
        f"- Override with environment variable: `{DOCS_ROOT_ENV}`",
        "",
        "## Topic Guides",
        "",
    ]
    for topic, guide in sorted(TOPIC_GUIDES.items()):
        docs = ", ".join(f"`{doc_id}`" for doc_id in guide["doc_ids"])
        lines.append(f"- `{topic}`: {guide['summary']} Docs: {docs}.")

    lines.extend(["", "## Official Documents", ""])
    for reference in OFFICIAL_REFERENCES:
        lines.append(f"- `{reference.doc_id}`: {reference.title} ({reference.version}, {reference.release_date})")
        lines.append(f"  - URL: {reference.url}")
        lines.append(f"  - Resource: {reference.resource_uri}")
        candidates = ", ".join(f"`{path}`" for path in _local_path_candidates(reference.local_filenames)) or "None"
        lines.append(f"  - Local path candidates: {candidates}")
        lines.append(f"  - Scope: {reference.scope}")
    return "\n".join(lines) + "\n"


def official_doc_resource(doc_id: str) -> str:
    reference = get_official_reference(doc_id)
    topics = ", ".join(f"`{topic}`" for topic in reference["topics"])
    use_when = "\n".join(f"- {item}" for item in reference["use_when"])
    filenames = ", ".join(f"`{name}`" for name in reference["local_filenames"]) or "None"
    candidates = "\n".join(f"- `{path}`" for path in reference["local_path_candidates"]) or "- None"
    available = "\n".join(f"- `{path}`" for path in reference["available_local_paths"]) or "- None found"
    return (
        f"# {reference['doc_id']}: {reference['title']}\n\n"
        f"- URL: {reference['url']}\n"
        f"- Version: {reference['version']}\n"
        f"- Release date: {reference['release_date']}\n"
        f"- Resource URI: {reference['resource_uri']}\n"
        f"- Local docs root: `{reference['local_docs_root']}`\n"
        f"- Local filename candidates: {filenames}\n"
        f"- Topics: {topics}\n\n"
        "## Local Path Candidates\n\n"
        f"{candidates}\n\n"
        "## Available Local Files\n\n"
        f"{available}\n\n"
        "## Scope\n\n"
        f"{reference['scope']}\n\n"
        "## Use When\n\n"
        f"{use_when}\n\n"
        "## Authority Note\n\n"
        f"{reference['authority_note']}\n"
    )


def local_docs_root() -> str:
    return os.environ.get(DOCS_ROOT_ENV, DEFAULT_LOCAL_DOCS_ROOT)


def normalize_topic(topic: str | None) -> str | None:
    normalized = (topic or "").strip().lower().replace("_", "-")
    if not normalized:
        return None
    return TOPIC_ALIASES.get(normalized, normalized)


def _find_reference(doc_id: str) -> OfficialReference:
    normalized = doc_id.strip().upper()
    for reference in OFFICIAL_REFERENCES:
        if reference.doc_id == normalized:
            return reference
    raise KeyError(f"Unknown official Vivado document {doc_id!r}")


def _terms(value: str | None) -> tuple[str, ...]:
    normalized = (value or "").strip().lower().replace("_", "-")
    if not normalized:
        return ()
    return tuple(term for term in normalized.split() if term)


def _reference_text(reference: OfficialReference) -> str:
    return " ".join(
        [
            reference.doc_id,
            reference.title,
            reference.scope,
            " ".join(reference.topics),
            " ".join(reference.use_when),
        ]
    ).lower()


def _local_path_candidates(filenames: tuple[str, ...]) -> list[str]:
    root = Path(local_docs_root())
    return [str(root / filename) for filename in filenames]
