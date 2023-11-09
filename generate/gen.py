"""
To generate the pages run:

python generate/gen.py generate/bugs.json templates ./
"""
import argparse
import json
import os

from collections import defaultdict
from datetime import datetime


reports_pre = """
<!DOCTYPE doctype PUBLIC "-//w3c//dtd html 4.0 transitional//en">
<html>
<head>
    <meta http-equiv="Content-Type"content="text/html; charset=iso-8859-1">
    <link rel="manifest" href="/site.webmanifest">
    <meta name="msapplication-TileColor" content="#da532c">
    <meta name="theme-color" content="#ffffff">
  <title>{}</title>
</head>


<body bgcolor="#ffffff">

<link type="text/css" rel="stylesheet" href="reports_style.css">

"""

reports_post = """

</body>
</html>
"""

details_resolution = """<br>
<b>Resolution</b>:
{}"""

details_resolution_date = """<br>
<b>Resolution date</b>:
{}"""

details_characteristics = """<b>Test Case Characteristics</b>:
{}"""

details_test = """<br>
<b>Test case</b>:
<pre>
<xmp>
{}
</xmp>
</pre>"""

details_fix = """<br>
<b>Fix Commit(s)</b>:
<ul>
{}
</ul>
"""

details = """
<details>
<br>
<b>Link</b>:
<a href="{link}">{link}</a>
<br>
<b>Date found</b>:
{date}
<br>
<b>Status</b>:
{status}
{resolution}
{resolution_date}
<br>
<b>Symptom</b>:
{symptom}
{test}
{characteristics}
{fix}
<br>
<br>
</details>
"""


features_lookup = {
    "Parameterized class": "Parametric polymorphism",
    "Parameterized type": "Parametric polymorphism",
    "Parameterized function": "Parametric polymorphism",
    "Use-site variance": "Parametric polymorphism",
    "Bounded type parameter": "Parametric polymorphism",
    "Declaration-site variance": "Parametric polymorphism",
    "Inheritance / Implementation of multiple interfaces": "OOP features",
    "Overriding": "OOP features",
    "Default method": "OOP features",
    "Inner class": "OOP features",
    "Access modifier": "OOP features",
    "Static method": "OOP features",
    "Recursive upper bound": "Bounded polymorphism",
    "Array type": "Type system-related features",
    "Subtyping": "Type system-related features",
    "Primitive type": "Type system-related features",
    "Wildcard type": "Type system-related features",
    "Nothing": "Type system-related features",
    "Nullable type": "Type system-related features",
    "Lambda": "Functional programming",
    "Function reference": "Functional programming",
    "Single Abstract Method (SAM)": "Functional programming",
    "Overloading": "Overloading",
    "Operator": "Standard language features",
    "Function type": "Functional programming",
    "Conditionals": "Standard language features",
    "Array": "Standard language features",
    "Cast": "Standard language features",
    "Variable argument": "Standard language features",
    "Type argument inference": "Type inference",
    "Variable type inference": "Type inference",
    "Bridge method": "Parametric polymophirsm",
    "Parameter type inference": "Type inference",
    "Flow typing": "Type inference",
    "Return type inference": "Type inference",
    "Named arguments": "Other"
}


lang_lookup = {
    'Groovy': 'groovyc',
    'Kotlin': 'kotlinc',
    'Java': 'javac',
    'Scala': 'scalac',
    'total': 'Total'
}


rows_lookup = {
    'generator': 'Generator',
    'inference': 'TEM',
    'soundness': 'TOM',
    'inference/soundness': 'TEM & TOM',
    'Unexpected Compile-Time Error': 'UCTE',
    'Unexpected Runtime Behavior': 'URB',
    'Compilation Performance Issue': 'CPI',
    'crash': 'Crash'
}


urls = {
    'Groovy': 'https://github.com/apache/groovy/commit/',
    'Kotlin': 'https://github.com/JetBrains/kotlin/commit/',
    'Java': 'https://github.com/openjdk/jdk/commit/',
    'Scala': 'https://github.com/lampepfl/dotty/commit/',
}


def get_args():
    parser = argparse.ArgumentParser(
        description='Generate html pages')
    parser.add_argument("input", help="JSON file with bugs.")
    parser.add_argument("templates", help="Directory with html templates.")
    parser.add_argument("output", help="Directory to save the pages.")
    return parser.parse_args()


def process(bug, res, bugs_by_mutator, chars, combinations, categories):
    d = {
        'status': {
            'Kotlin': {
                'Submitted': 'Reported',
                'In Progress': 'Confirmed',
                'Open': 'Confirmed',
                'Closed': None
            },
            'Groovy': {
                'Open': 'Confirmed',
                'In Progress': 'Confirmed',
                'Resolved': None,
                'Reopened': 'Confirmed',
                'Closed': None
            },
            'Java': {
                'New': 'Confirmed',
                'Closed': None,
                'Resolved': None,
                'Open': 'Confirmed'
            },
            'Scala': {
                'Open': 'Confirmed',
                'In Progress': 'Confirmed',
                'Closed': None
            }
        },
        'resolution': {
            'Kotlin': {
                'Fixed': 'Fixed',
                'Obsolete': 'Fixed',
                'As Designed': 'Wont fix',
                'Duplicate': 'Duplicate'
            },
            'Groovy': {
                'Duplicate': 'Duplicate',
                'Fixed': 'Fixed',
                'Information Provided': 'Wont fix',
                "Won't Fix": "Wont fix",
                'Closed': None
            },
            'Java': {
                'Not an Issue':  'Wont fix',
                'Duplicate': 'Duplicate',
                'Fixed': 'Fixed'
            },
            'Scala': {
                'Not an Issue':  'Wont fix',
                'Duplicate': 'Duplicate',
                'Fixed': 'Fixed'
            }
        },
        'symptom': {
            'Unexpected Compile-Time Error': 'Unexpected Compile-Time Error',
            'Unexpected Runtime Behavior': 'Unexpected Runtime Behavior',
            'crash': 'crash',
            'Compilation Performance Issue': 'Compilation Performance Issue',
            'Misleading Report': 'Unexpected Compile-Time Error'
        },
    }
    lang = bug['language']
    bstatus = bug['status']
    bresolution = bug['resolution']
    bsymptom = bug['symptom']
    bmutator = bug['mutator']
    status = d['status'][lang].get(bstatus, None)
    if status is None:
        status = d['resolution'][lang].get(bresolution, None)
    symptom = d['symptom'].get(bsymptom, None)
    if status is None:
        import pdb; pdb.set_trace()
    res[lang]['status'][status] += 1
    res[lang]['symptom'][symptom] += 1
    res[lang]['mutator'][bmutator] += 1
    res['total']['status'][status] += 1
    res['total']['symptom'][symptom] += 1
    res['total']['mutator'][bmutator] += 1

    bugs_by_mutator[bmutator][lang].append(bug)

    bcategories = set()
    for char in bug['chars']['characteristics']:
        bcategories.add(features_lookup[char])
        chars[char] += 1
        mcategories = set()
        for comb in bug['chars']['characteristics']:
            if char != comb:
                mcategories.add(features_lookup[comb])
        for cat in mcategories:
            combinations[char][cat] += 1
    for c in bcategories:
        categories[c] += 1


def create_index(templates, output, res):
    # Read template
    index_template = os.path.join(templates, 'index.html')
    with open(index_template, 'r') as f:
        index = f.read()
    # Process
    to_replace = {
            'TOTAL_BUGS': sum(v for v in res['total']['status'].values()),
            'TOTAL_FIXED': res['total']['status']['Fixed']
    }
    for lang in ('Groovy', 'Kotlin', 'Java', 'Scala'):
        to_replace[lang.upper() + '_BUGS'] = sum(
            v for v in res[lang]['status'].values())
        to_replace[lang.upper() + '_FIXED'] = res[lang]['status']['Fixed']

    symptoms = [('Unexpected Compile-Time Error', 'UCTE'),
                ('Unexpected Runtime Behavior', 'URB'),
                ('Compilation Performance Issue', 'CPI'),
                ('crash', 'CRASH')]
    for symptom, keyword in symptoms:
        to_replace[keyword + '_BUGS'] = res['total']['symptom'][symptom]

    components = [('generator', 'HEPHAESTUS'),
                  ('inference', 'TEM'),
                  ('soundness', 'TOM'),
                  ('inference/soundness', 'COMB')]
    for component, keyword in components:
        to_replace[keyword + '_BUGS'] = res['total']['mutator'][component]

    to_replace['LAST_MODIFIED'] = datetime.today().strftime('%Y-%m-%d')

    for k, v in to_replace.items():
        k = "{{{{{}}}}}".format(k)
        index = index.replace(k, str(v))
    # Write result
    index_page = os.path.join(output, 'index.html')
    with open(index_page, 'w') as f:
        f.write(index)


def create_bug_reports(component, bugs, output, filename):
    out = os.path.join(output, filename)
    contents = []

    title = "Bug findings with {}".format(component)
    title_header = "<h2>{}</h2>\n\n".format(title)
    contents.append(reports_pre.format(title))
    contents.append(title_header)

    counter = 1
    for lang, lang_bugs in bugs.items():
        contents.append("<h3>{}</h3>\n\n".format(lang))
        contents.append("<ul>\n")
        for bug in lang_bugs:
            bug_details = details.format(
                link=bug['links']['issuetracker'],
                date=bug['date'].split(' ')[0],
                status=bug['status'],
                resolution='' if not bug['resolution'] else
                           details_resolution.format(bug['resolution']),
                resolution_date='' if bug['resolutiondate'] == 'None' else
                                details_resolution_date.format(
                                    bug['resolutiondate'].split(' ')[0]
                                ),
                symptom=bug['symptom'].capitalize(),
                characteristics='' if len(bug['chars']['characteristics']) == 0
                                else details_characteristics.format(
                                    ", ".join(bug['chars']['characteristics'])
                                ),
                test='' if len(bug['test']) == 0 else
                     details_test.format("\n".join(bug['test'])),
                fix='' if not bug.get('fix', False) else
                    details_fix.format("".join(
                        ["<li>\n<a href='{url}'>{url}</a>\n</li>\n".format(
                            url = urls[lang] + i)
                         for i in bug['fix']['commits']]
                    ))
            )
            contents.append("<li>\n<b>\n#{} {} {}\n</b>\n{}</li>\n".format(
               counter, bug['title'],
               '' if bug['resolution'] != 'Fixed' else ' -- Fixed',
               bug_details
            ))
            counter += 1
        contents.append("</ul>\n\n")

    contents.append(reports_post)

    with open(out, 'w') as f:
        f.writelines(contents)


def main():
    args = get_args()
    with open(args.input, 'r') as f:
        data = json.load(f)
    chars = defaultdict(lambda: 0)
    combinations = defaultdict(lambda: defaultdict(lambda: 0))
    res = defaultdict(lambda: {
        'status': {
            'Reported': 0,
            'Confirmed': 0,
            'Fixed': 0,
            'Wont fix': 0,
            'Duplicate': 0
        },
        'symptom': {
            'Unexpected Compile-Time Error': 0,
            'Unexpected Runtime Behavior': 0,
            'Compilation Performance Issue': 0,
            'crash': 0
        },
        'mutator': {
            'generator': 0,
            'inference': 0,
            'soundness': 0,
            'inference/soundness': 0
        }
    })
    bugs_by_mutator = {
        'generator': defaultdict(list),
        'inference': defaultdict(list),
        'soundness': defaultdict(list),
        'inference/soundness': defaultdict(list),
    }
    categories = defaultdict(lambda: 0)
    for bug in data:
        process(bug, res, bugs_by_mutator, chars, combinations, categories)
    langs = ['Groovy', 'Kotlin', 'Java', 'Scala', 'total']

    create_index(args.templates, args.output, res)
    create_bug_reports('Program Generator', bugs_by_mutator['generator'],
                       args.output, 'hephaestus_bugs.html')
    create_bug_reports('Type Erasure Mutation', bugs_by_mutator['inference'],
                       args.output, 'tem_bugs.html')
    create_bug_reports('Type Overwriting Mutation', bugs_by_mutator['soundness'],
                       args.output, 'tom_bugs.html')
    create_bug_reports('Type Erasure and Type Overwriting Mutation',
                       bugs_by_mutator['inference/soundness'],
                       args.output, 'tem_tom_bugs.html')


if __name__ == "__main__":
    main()
