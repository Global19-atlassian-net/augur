"""
The top-level augur command which dispatches to subcommands.
"""

import argparse
from sys import exit
from types import SimpleNamespace
from . import parse, filter, align, tree, refine, ancestral
from . import traits, translate, mask, titers, export
from . import validate, sequence_traits, clades, version


def run(argv):
    parser = argparse.ArgumentParser(prog = "augur", description = "Augur: Real-Time Phylogenetic analysis.")
    subparsers = parser.add_subparsers()

    add_version_alias(parser)

    ### PARSE.PY -- produce a pair of tsv/fasta files from a single fasta file
    parse_parser = subparsers.add_parser('parse', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parse_parser.add_argument('--sequences', '-s', required=True, help="sequences in fasta or VCF format")
    parse_parser.add_argument('--output-sequences', help="output sequences file")
    parse_parser.add_argument('--output-metadata', help="output metadata file")
    parse_parser.add_argument('--fields', nargs='+', help="fields in fasta header")
    parse_parser.add_argument('--separator', default='|', help="separator of fasta header")
    parse_parser.add_argument('--fix-dates', choices=['dayfirst', 'monthfirst'],
                                help="attempt to parse non-standard dates and output them in standard YYYY-MM-DD format")
    parse_parser.set_defaults(func=parse.run)

    ### FILTER.PY -- filter and subsample an sequence set
    filter_parser = subparsers.add_parser('filter', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    filter_parser.add_argument('--sequences', '-s', required=True, help="sequences in fasta or VCF format")
    filter_parser.add_argument('--metadata', required=True, help="metadata associated with sequences")
    filter_parser.add_argument('--min-date', type=float, help="minimal cutoff for numerical date")
    filter_parser.add_argument('--max-date', type=float, help="maximal cutoff for numerical date")
    filter_parser.add_argument('--min-length', type=int, help="minimal length of the sequences")
    filter_parser.add_argument('--exclude', type=str, help="file with list of strains that are to be excluded")
    filter_parser.add_argument('--include', type=str, help="file with list of strains that are to be included regardless of priorities or subsampling")
    filter_parser.add_argument('--priority', type=str, help="file with list priority scores for sequences (strain\tpriority)")
    filter_parser.add_argument('--sequences-per-group', type=int, help="subsample to no more than this number of sequences per category")
    filter_parser.add_argument('--group-by', nargs='+', help="categories with respect to subsample; two virtual fields, \"month\" and \"year\", are supported if they don't already exist as real fields but a \"date\" field does exist")
    filter_parser.add_argument('--exclude-where', nargs='+',
                                help="Exclude samples with these values. ex: host=rat. Multiple values are processed as OR (having any of those specified will be excluded), not AND")
    filter_parser.add_argument('--include-where', nargs='+',
                                help="Include samples with these values. ex: host=rat. Multiple values are processed as OR (having any of those specified will be included), not AND")
    filter_parser.add_argument('--output', '-o', help="output file")
    filter_parser.set_defaults(func=filter.run)

    ### MASK.PY -- mask specified sites from a VCF file
    mask_parser = subparsers.add_parser('mask', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    mask_parser.add_argument('--sequences', '-s', required=True, help="sequences in VCF format")
    mask_parser.add_argument('--mask', required=True, help="locations to be masked in BED file format")
    mask_parser.add_argument('--output', '-o', help="output file")
    mask_parser.set_defaults(func=mask.run)

    ### ALIGN.PY
    align_parser = subparsers.add_parser('align', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    align_parser.add_argument('--sequences', '-s', required=True, help="sequences in fasta or VCF format")
    align_parser.add_argument('--output', '-o', help="output file")
    align_parser.add_argument('--nthreads', type=int, default=2,
                                help="number of threads used")
    align_parser.add_argument('--method', default='mafft', choices=["mafft"],
                                help="alignment program to use")
    align_parser.add_argument('--reference-name', type=str, help="strip insertions relative to reference sequence; use if the reference is already in the input sequences")
    align_parser.add_argument('--reference-sequence', type=str, help="strip insertions relative to reference sequence; use if the reference is NOT already in the input sequences")
    align_parser.add_argument('--remove-reference', action="store_true", default=False, help="remove reference sequence from the alignment")
    align_parser.add_argument('--fill-gaps', action="store_true", default=False, help="if gaps represent missing data rather than true indels, replace by N after aligning")
    align_parser.set_defaults(func=align.run)

    ## TREE.PY
    tree_parser = subparsers.add_parser('tree', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    tree_parser.add_argument('--alignment', '-a', required=True, help="alignment in fasta or VCF format")
    tree_parser.add_argument('--method', default='iqtree', choices=["fasttree", "raxml", "iqtree"], help="tree builder to use")
    tree_parser.add_argument('--output', '-o', type=str, help='file name to write tree to')
    tree_parser.add_argument('--substitution-model', default="GTR", choices=["HKY", "GTR", "HKY+G", "GTR+G"],
                                help='substitution model to use. Specify \'none\' to run ModelTest. Currently, only available for IQTREE.')
    tree_parser.add_argument('--nthreads', type=int, default=2,
                             help="number of threads used")
    tree_parser.add_argument('--vcf-reference', type=str, help='fasta file of the sequence the VCF was mapped to')
    tree_parser.add_argument('--exclude-sites', type=str, help='file name of sites to exclude for raw tree building (VCF only)')
    tree_parser.set_defaults(func=tree.run)


    ## REFINE.PY
    refine_parser = subparsers.add_parser('refine', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    refine_parser.add_argument('--alignment', '-a', help="alignment in fasta or VCF format")
    refine_parser.add_argument('--tree', '-t', required=True, help="prebuilt Newick")
    refine_parser.add_argument('--metadata', type=str, help="tsv/csv table with meta data for sequences")
    refine_parser.add_argument('--output-tree', type=str, help='file name to write tree to')
    refine_parser.add_argument('--output-node-data', type=str, help='file name to write branch lengths as node data')
    refine_parser.add_argument('--timetree', action="store_true", help="produce timetree using treetime")
    refine_parser.add_argument('--coalescent', help="coalescent time scale in units of inverse clock rate (float), optimize as scalar ('opt'), or skyline ('skyline')")
    refine_parser.add_argument('--clock-rate', type=float, help="fixed clock rate")
    refine_parser.add_argument('--root', nargs="+", help="rooting mechanism ('best', 'residual', 'rsq', 'min_dev') "
                                "OR node to root by OR two nodes indicating a monophyletic group to root by")
    refine_parser.add_argument('--date-format', default="%Y-%m-%d", help="date format")
    refine_parser.add_argument('--date-confidence', action="store_true", help="calculate confidence intervals for node dates")
    refine_parser.add_argument('--date-inference', default='joint', choices=["joint", "marginal"],
                                help="assign internal nodes to their marginally most likely dates, not jointly most likely")
    refine_parser.add_argument('--branch-length-inference', default='auto', choices = ['auto', 'joint', 'marginal', 'input'],
                                help='branch length mode of treetime to use')
    refine_parser.add_argument('--clock-filter-iqd', type=float, help='clock-filter: remove tips that deviate more than n_iqd '
                                'interquartile ranges from the root-to-tip vs time regression')
    refine_parser.add_argument('--nthreads', type=int, default=2,
                                help="number of threads used")
    refine_parser.add_argument('--vcf-reference', type=str, help='fasta file of the sequence the VCF was mapped to')
    refine_parser.add_argument('--year-bounds', type=int, nargs='+', help='specify min or max & min prediction bounds for samples with XX in year')
    refine_parser.set_defaults(func=refine.run)

    ## ANCESTRAL.PY
    ancestral_parser = subparsers.add_parser('ancestral', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ancestral_parser.add_argument('--tree', '-t', required=True, help="prebuilt Newick")
    ancestral_parser.add_argument('--alignment', '-a', help="alignment in fasta or VCF format")
    ancestral_parser.add_argument('--output', '-o', type=str, help='file name to save mutations and ancestral sequences to')
    ancestral_parser.add_argument('--inference', default='joint', choices=["joint", "marginal"],
                                    help="calculate joint or marginal maximum likelihood ancestral sequence states")
    ancestral_parser.add_argument('--vcf-reference', type=str, help='fasta file of the sequence the VCF was mapped to')
    ancestral_parser.add_argument('--output-vcf', type=str, help='name of output VCF file which will include ancestral seqs')
    ancestral_parser.set_defaults(func=ancestral.run)

    ## TRANSLATE.PY
    translate_parser = subparsers.add_parser('translate', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    translate_parser.add_argument('--tree', help="prebuilt Newick -- no tree will be built if provided")
    translate_parser.add_argument('--ancestral-sequences', type=str, help='JSON (fasta input) or VCF (VCF input) containing ancestral and tip sequences')
    translate_parser.add_argument('--reference-sequence', required=True,
                        help='GenBank or GFF file containing the annotation')
    translate_parser.add_argument('--genes', nargs='+', help="genes to translate (list or file containing list)")
    translate_parser.add_argument('--output', type=str, help="name of JSON files for aa mutations")
    translate_parser.add_argument('--alignment-output', type=str, help="write out translated gene alignments. "
                                   "If a VCF-input, a .vcf or .vcf.gz will be output here (depending on file ending). If fasta-input, specify the file name "
                                   "like so: 'my_alignment_%GENE.fasta', where '%GENE' will be replaced by the name of the gene")
    translate_parser.add_argument('--vcf-reference-output', type=str, help="fasta file where reference sequence translations for VCF input will be written")
    translate_parser.add_argument('--vcf-reference', type=str, help='fasta file of the sequence the VCF was mapped to')
    translate_parser.set_defaults(func=translate.run)

    ## CLADES.PY
    clades_parser = subparsers.add_parser('clades', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    clades_parser.add_argument('--tree', help="prebuilt Newick -- no tree will be built if provided")
    clades_parser.add_argument('--mutations', nargs='+', help='JSON(s) containing ancestral and tip nucleotide and/or amino-acid mutations ')
    clades_parser.add_argument('--clades', type=str, help='TSV file containing clade definitions by amino-acid')
    clades_parser.add_argument('--output', type=str, help="name of JSON files for clades")
    clades_parser.set_defaults(func=clades.run)

    ## TRAITS.PY
    traits_parser = subparsers.add_parser('traits', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    traits_parser.add_argument('--tree', '-t', required=True, help="tree to perform trait reconstruction on")
    traits_parser.add_argument('--metadata', required=True, help="tsv/csv table with meta data")
    traits_parser.add_argument('--columns', required=True, nargs='+',
                        help='metadata fields to perform discrete reconstruction on')
    traits_parser.add_argument('--confidence',action="store_true",
                        help='record the distribution of subleading mugration states')
    traits_parser.add_argument('--output', '-o', default='traits.json', help='')
    traits_parser.set_defaults(func=traits.run)

    ## SEQUENCE_TRAITS.PY
    map_parser = subparsers.add_parser('sequence-traits', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    map_parser.add_argument('--ancestral-sequences', type=str, help="nucleotide alignment to search for sequence traits in")
    map_parser.add_argument('--translations', type=str, help="AA alignment to search for sequence traits in (can include ancestral sequences)")
    map_parser.add_argument('--vcf-reference', type=str, help='fasta file of the sequence the nucleotide VCF was mapped to')
    map_parser.add_argument('--vcf-translate-reference', type=str, help='fasta file of the sequence the translated VCF was mapped to')
    map_parser.add_argument('--features', type=str, help='file that specifies sites defining the features in a tab-delimited format "GENOMIC_POSITION ALT_BASE DRUG AA(optional)"')
    map_parser.add_argument('--count', type=str, choices=['traits','mutations'], default='traits', help='Whether to count traits (ex: # drugs resistant to) or mutations')
    map_parser.add_argument('--label', type=str, default="# Traits", help='How to label the counts (ex: Drug_Resistance)')
    map_parser.add_argument('--output', '-o', type=str, help='output json with sequence features')
    map_parser.set_defaults(func=sequence_traits.run)

    ## TITERS.PY
    titers_parser = subparsers.add_parser('titers', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    titers_parser.add_argument('--titers', required=True, type=str, help="file with titer measurements")
    titers_parser.add_argument('--tree', '-t', type=str, required=True, help="tree to perform fit titer model to")
    titers_parser.add_argument('--titer-model', default='substitution', choices=["substitution", "tree"],
                                help="titer model to use, see Neher et al. 2016 for details")
    titers_parser.add_argument('--output', '-o', type=str, help='JSON file to save titer model')
    titers_parser.set_defaults(func=titers.run)

    ## EXPORT.PY
    export_parser =  subparsers.add_parser("export", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    export_parser.add_argument('--tree', '-t', required=True, help="tree to perform trait reconstruction on")
    export_parser.add_argument('--metadata', required=True, help="tsv file with sequence meta data")
    export_parser.add_argument('--reference', required=False, help="reference sequence for export to browser, only vcf")
    export_parser.add_argument('--reference-translations', required=False, help="reference translations for export to browser, only vcf")
    export_parser.add_argument('--node-data', required=True, nargs='+', help="JSON files with meta data for each node")
    export_parser.add_argument('--auspice-config', help="file with auspice configuration")
    export_parser.add_argument('--colors', help="file with color definitions")
    export_parser.add_argument('--lat-longs', help="file latitudes and longitudes, overrides built in mappings")
    export_parser.add_argument('--new-schema', action="store_true", help="export JSONs using nexflu schema")
    export_parser.add_argument('--output-main', help="Main JSON file name that is passed on to auspice (e.g., zika.json).")
    export_parser.add_argument('--output-tree', help="JSON file name that is passed on to auspice (e.g., zika_tree.json). Only used with --nextflu-schema")
    export_parser.add_argument('--output-sequence', help="JSON file name that is passed on to auspice (e.g., zika_seq.json). Only used with --nextflu-schema")
    export_parser.add_argument('--output-meta', help="JSON file name that is passed on to auspice (e.g., zika_meta.json). Only used with --nextflu-schema")
    export_parser.add_argument('--title', default="Analysis", help="Title to be displayed by auspice")
    export_parser.add_argument('--maintainers', default=[""], nargs='+', help="Analysis maintained by")
    export_parser.add_argument('--maintainer-urls', default=[""], nargs='+', help="URL of maintainers")
    export_parser.add_argument('--geography-traits', nargs='+', help="What location traits are used to plot on map")
    export_parser.add_argument('--extra-traits', nargs='+', help="Metadata columns not run through 'traits' to be added to tree")
    export_parser.add_argument('--panels', default=['tree', 'map', 'entropy'], nargs='+', help="What panels to display in auspice. Options are : xxx")
    export_parser.set_defaults(func=export.run)

    ## VALIDATE.PY
    validate_parser = subparsers.add_parser('validate', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    validate_parser.add_argument('--json', required=True, nargs='+', help="JSONs to validate")
    validate_parser.add_argument('--new-schema', action="store_true", help="use nexflu JSON schema")
    validate_parser.set_defaults(func=validate.run)

    ## VERSION.PY
    version_parser = subparsers.add_parser(
        "version",
        description     = version.__doc__,
        formatter_class = argparse.ArgumentDefaultsHelpFormatter)

    version_parser.set_defaults(func=version.run)

    args = parser.parse_args(argv)
    return args.func(args)


def add_version_alias(parser):
    """
    Add --version as a (hidden) alias for the version command.

    It's not uncommon to blindly run a command with --version as the sole
    argument, so its useful to make that Just Work.
    """

    class run_version_command(argparse.Action):
        def __call__(self, *args, **kwargs):
            opts = SimpleNamespace()
            exit( version.run(opts) )

    return parser.add_argument(
        "--version",
        nargs  = 0,
        help   = argparse.SUPPRESS,
        action = run_version_command)
