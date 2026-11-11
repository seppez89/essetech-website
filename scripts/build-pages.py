#!/usr/bin/env python3
"""Build the "one page per question" service pages.

Each page here answers one thing people ask a search engine or an AI
assistant ("who can set up Microsoft Copilot in Adelaide?"), with the scope,
price, timeframe and prerequisites stated plainly. The header, footer, styles
and scripts are copied from fractional-it-manager-adelaide.html so these pages
always match the rest of the site.

Order to run things in (from the repo root):

    python3 scripts/build-pages.py        # writes the pages
    python3 scripts/key-facts.py          # adds the key-facts panel
    python3 scripts/footer-links.py       # keeps the footer the same everywhere
    python3 scripts/schema-identity.py    # fills in the business details
    npx tailwindcss@3.4.17 -c tailwind.config.js -i tailwind-input.css -o tailwind.css --minify

Prices must match pricing-adelaide.html. Don't add a claim here that isn't
already true and published.
"""
import html
import json
import re
import sys

BASE = "https://www.essetech.com.au"
SHELL = "fractional-it-manager-adelaide.html"
ARROW = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>'
PHONE = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>'
TICK = '<svg class="w-5 h-5 text-fire-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
LINK = 'class="font-semibold text-fire-600 underline hover:text-fire-700"'
WHERE = "No. We work in person across the Adelaide metro area from our base in Brooklyn Park, and remotely with businesses anywhere in Australia."


# ---------------------------------------------------------------- sections

def hero(badge, h1, lead, cta):
    return f'''
    <!-- HERO -->
    <section class="hero-mesh bg-navy-900 pt-32 pb-20 md:pt-40 md:pb-28 relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-navy-900 via-navy-800 to-navy-700 opacity-40"></div>
        <div class="absolute top-1/3 left-0 w-96 h-96 bg-navy-500/15 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 right-0 w-80 h-80 bg-fire-500/10 rounded-full blur-3xl"></div>
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
        <div class="orb orb-4"></div>
        <div class="orb orb-5"></div>
        <div class="particles" id="particles"></div>
        <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="max-w-3xl">
                <div class="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-5 py-2 mb-8">
                    <span class="w-2 h-2 bg-fire-400 rounded-full animate-pulse"></span>
                    <span class="text-sm text-white/80 font-medium">{badge}</span>
                </div>
                <h1 class="text-4xl sm:text-5xl md:text-6xl font-black text-white leading-[1.05] tracking-tight">{h1}</h1>
                <p class="mt-7 text-lg sm:text-xl text-white/70 leading-relaxed max-w-2xl">{lead}</p>
                <div class="mt-10 flex flex-col sm:flex-row gap-4">
                    <a href="https://www.essetech.com.au/#contact" class="btn-shimmer inline-flex items-center justify-center gap-2 bg-fire-500 text-white px-8 py-4 rounded-full text-base font-bold">{cta} {ARROW}</a>
                    <a href="tel:0404311791" class="inline-flex items-center justify-center gap-2 border border-white/20 text-white px-8 py-4 rounded-full text-base font-semibold hover:bg-white/5 transition-all duration-300">{PHONE} 0404 311 791</a>
                </div>
            </div>
        </div>
    </section>
'''


def split(sid, h2, paragraphs, box_title, items, tint=False):
    paras = "\n".join(
        f'                    <p class="mt-{6 if i == 0 else 4} text-gray-600 leading-relaxed{" text-lg" if i == 0 else ""}">{p}</p>'
        for i, p in enumerate(paragraphs))
    lis = "\n".join(
        f'                            <li class="flex items-start gap-3">{TICK}<span class="text-gray-700 leading-relaxed">{item}</span></li>'
        for item in items)
    return f'''
    <section id="{sid}" class="py-20 md:py-28{" bg-navy-50" if tint else ""}">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid lg:grid-cols-2 gap-16 items-center">
                <div class="reveal">
                    <h2 class="text-3xl md:text-4xl font-bold text-navy-900 leading-tight">{h2}</h2>
{paras}
                </div>
                <div class="reveal">
                    <div class="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
                        <h3 class="font-bold text-navy-900 text-lg">{box_title}</h3>
                        <ul class="mt-5 space-y-4">
{lis}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </section>
'''


def cards(sid, h2, intro, items, tint=False, cols=3):
    grid = {2: "md:grid-cols-2", 3: "md:grid-cols-2 lg:grid-cols-3", 4: "sm:grid-cols-2 xl:grid-cols-4"}[cols]
    body = "\n".join(
        f'''                <div class="service-card bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
                    <h3 class="font-bold text-navy-900 text-lg">{title}</h3>
                    <p class="mt-3 text-gray-600 leading-relaxed">{text}</p>
                </div>''' for title, text in items)
    return f'''
    <section id="{sid}" class="py-20 md:py-28{" bg-navy-50" if tint else ""}">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16 reveal">
                <h2 class="text-3xl md:text-4xl font-bold text-navy-900">{h2}</h2>
                <p class="mt-4 text-gray-600 leading-relaxed">{intro}</p>
            </div>
            <div class="grid {grid} gap-6 reveal">
{body}
            </div>
        </div>
    </section>
'''


def steps(sid, h2, intro, items, tint=False):
    body = "\n".join(
        f'''                <li class="flex items-start gap-5 bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-100">
                    <span class="flex-shrink-0 w-10 h-10 rounded-full bg-fire-500 text-white font-bold flex items-center justify-center">{n}</span>
                    <div>
                        <h3 class="font-bold text-navy-900 text-lg">{title}</h3>
                        <p class="mt-2 text-gray-600 leading-relaxed">{text}</p>
                    </div>
                </li>''' for n, (title, text) in enumerate(items, 1))
    return f'''
    <section id="{sid}" class="py-20 md:py-28{" bg-navy-50" if tint else ""}">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16 reveal">
                <h2 class="text-3xl md:text-4xl font-bold text-navy-900">{h2}</h2>
                <p class="mt-4 text-gray-600 leading-relaxed">{intro}</p>
            </div>
            <ol class="space-y-4 reveal">
{body}
            </ol>
        </div>
    </section>
'''


def prices(sid, h2, intro, items, note, tint=False):
    body = "\n".join(
        f'''                <div class="service-card bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
                    <h3 class="font-bold text-navy-900 text-lg">{title}</h3>
                    <p class="text-gray-500 text-sm mt-1">{sub}</p>
                    <div class="mt-5 text-4xl font-black text-navy-900">{price}</div>
                    <p class="text-gray-500 text-sm mt-1">{unit}</p>
                </div>''' for title, sub, price, unit in items)
    return f'''
    <section id="{sid}" class="py-20 md:py-28{" bg-navy-50" if tint else ""}">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16 reveal">
                <h2 class="text-3xl md:text-4xl font-bold text-navy-900">{h2}</h2>
                <p class="mt-4 text-gray-600">{intro}</p>
            </div>
            <div class="grid md:grid-cols-3 gap-6 reveal">
{body}
            </div>
            <p class="mt-8 max-w-3xl mx-auto text-center text-gray-600 leading-relaxed reveal">{note}</p>
        </div>
    </section>
'''


def table(sid, h2, intro, headers, rows, note="", tint=False):
    head = "".join(f'<th scope="col" class="px-5 py-4 text-left text-sm font-bold text-navy-900">{h}</th>' for h in headers)
    body = "\n".join(
        '                        <tr class="border-t border-gray-100">'
        + "".join(
            (f'<th scope="row" class="px-5 py-4 text-left text-sm font-semibold text-navy-900">{cell}</th>' if i == 0
             else f'<td class="px-5 py-4 text-sm text-gray-600 leading-relaxed">{cell}</td>')
            for i, cell in enumerate(row))
        + "</tr>" for row in rows)
    after = f'\n            <p class="mt-8 text-center text-gray-600 leading-relaxed reveal">{note}</p>' if note else ""
    return f'''
    <section id="{sid}" class="py-20 md:py-28{" bg-navy-50" if tint else " border-t border-gray-100"}">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-12 reveal">
                <h2 class="text-3xl md:text-4xl font-bold text-navy-900">{h2}</h2>
                <p class="mt-4 text-gray-600 leading-relaxed">{intro}</p>
            </div>
            <div class="table-wrap bg-white rounded-2xl shadow-sm border border-gray-100 reveal">
                <table class="compare-table w-full">
                    <thead><tr class="bg-navy-50">{head}</tr></thead>
                    <tbody>
{body}
                    </tbody>
                </table>
            </div>{after}
        </div>
    </section>
'''


def faq(h2, intro, items):
    body = "\n".join(
        f'''                <div class="faq-item bg-white rounded-2xl p-6">
                    <button class="faq-toggle flex items-center justify-between w-full text-left">
                        <span class="font-semibold text-navy-900 pr-4">{q}</span>
                        <span class="faq-icon flex-shrink-0 w-8 h-8 bg-navy-50 rounded-full flex items-center justify-center text-navy-500 font-bold text-xl leading-none">+</span>
                    </button>
                    <div class="faq-answer text-gray-600 text-sm leading-relaxed">
                        {html.escape(a, quote=False)}
                    </div>
                </div>''' for q, a in items)
    return f'''
    <!-- FAQ -->
    <section id="faq" class="py-20 md:py-28 bg-navy-50">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center mb-16 reveal">
                <h2 class="text-3xl md:text-4xl font-bold text-navy-900">{h2}</h2>
                <p class="mt-4 text-gray-600">{intro}</p>
            </div>
            <div class="space-y-4 reveal">
{body}
            </div>
        </div>
    </section>
'''


def cta(h2, text, button):
    return f'''
    <!-- CTA -->
    <section id="contact" class="py-20 md:py-28 bg-gradient-to-br from-navy-800 via-navy-900 to-navy-800 relative overflow-hidden">
        <div class="absolute top-0 right-0 w-96 h-96 bg-fire-500/10 rounded-full blur-3xl"></div>
        <div class="absolute bottom-0 left-0 w-80 h-80 bg-navy-500/10 rounded-full blur-3xl"></div>
        <div class="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-3xl md:text-4xl font-bold text-white">{h2}</h2>
            <p class="mt-6 text-lg text-white/70 leading-relaxed">{text}</p>
            <p class="mt-4 text-white/70 leading-relaxed">Call <a href="tel:0404311791" class="font-semibold text-white hover:text-fire-400">0404 311 791</a> or email <a href="mailto:support@essetech.com.au" class="font-semibold text-white hover:text-fire-400">support@essetech.com.au</a>.</p>
            <div class="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
                <a href="https://www.essetech.com.au/#contact" class="btn-shimmer inline-flex items-center justify-center gap-2 bg-fire-500 text-white px-8 py-4 rounded-full text-base font-bold">{button} {ARROW}</a>
                <a href="tel:0404311791" class="inline-flex items-center justify-center gap-2 border border-white/20 text-white px-8 py-4 rounded-full text-base font-semibold hover:bg-white/5 transition-all duration-300">Call 0404 311 791</a>
            </div>
        </div>
    </section>
'''


def explore(items):
    body = "\n".join(
        f'''                <a href="{href}" class="bg-white rounded-xl p-5 text-center border border-gray-100 hover:border-navy-200 hover:shadow-md transition-all duration-300">
                    <div class="font-semibold text-navy-900 text-sm">{title}</div>
                    <div class="text-xs text-gray-500 mt-1">{sub}</div>
                </a>''' for href, title, sub in items)
    return f'''
    <section class="py-16 bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-2xl font-bold text-navy-900 text-center mb-10">Related services</h2>
            <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
{body}
            </div>
        </div>
    </section>
'''


def related(items):
    body = "\n".join(f'                <li><a href="{href}" class="font-semibold text-fire-600 hover:underline">{text}</a></li>' for href, text in items)
    return f'''
    <section class="py-10 bg-white" aria-labelledby="related-reading">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 id="related-reading" class="text-lg font-bold text-navy-900">Related reading</h2>
            <ul class="mt-4 space-y-2 text-sm">
{body}
            </ul>
        </div>
    </section>
'''


# ------------------------------------------------------------------- pages

SERVICES = {
    "copilot": ("/microsoft-copilot-consultant-adelaide.html", "Microsoft Copilot Setup", "Licences, permissions and training"),
    "ai": ("/ai-consultant-adelaide.html", "AI Consultant", "Find, build and run the right AI"),
    "e8": ("/essential-eight-adelaide.html", "Essential Eight", "The eight controls, put in place"),
    "m365": ("/microsoft-365-support-adelaide.html", "Microsoft 365 Support", "Email, Teams and SharePoint"),
    "consulting": ("/it-consulting-adelaide.html", "IT Consulting", "Reviews, planning and advice"),
    "enablement": ("/secure-ai-enablement-adelaide.html", "Secure AI Enablement", "Copilot and Claude, rolled out safely"),
    "growth": ("/ai-growth-system-adelaide.html", "AI Growth System", "AI call answering and follow-up"),
    "managed": ("/managed-it-services-adelaide.html", "Managed IT", "From $99 per user per month"),
    "support": ("/it-support-adelaide.html", "IT Support", "$150 an hour, no contract"),
    "cyber": ("/cybersecurity-adelaide.html", "Cybersecurity", "Protect your business"),
    "cloud": ("/cloud-solutions-adelaide.html", "Cloud Solutions", "Microsoft 365 and Azure migrations"),
    "fractional": ("/fractional-it-manager-adelaide.html", "Fractional IT Manager", "Part-time IT leadership"),
    "pricing": ("/pricing-adelaide.html", "Pricing", "Every price, published"),
}


def pick(*keys):
    return [SERVICES[k] for k in keys]


PAGES = []

# ---- Microsoft Copilot -----------------------------------------------------
PAGES.append({
    "file": "microsoft-copilot-consultant-adelaide.html",
    "crumb": "Microsoft Copilot Setup Adelaide",
    "title": "Microsoft Copilot Setup Adelaide | From $2,500 | Essetech",
    "description": "Microsoft Copilot set up safely for Adelaide businesses: licences, a file permissions clean-up, an AI use policy and staff training. From $2,500 + GST.",
    "service": {
        "name": "Microsoft Copilot Setup and Training Adelaide",
        "type": ["Microsoft Copilot deployment", "AI training"],
        "description": "Microsoft Copilot (formerly Microsoft 365 Copilot) set up for Adelaide businesses: licence and readiness check, file permissions clean-up, AI use policy and staff training. A typical rollout takes 4 to 6 weeks.",
        "offer": {"minPrice": 2500, "description": "Copilot rollout from $2,500 + GST. AI use policy and staff training from $1,100 + GST. Microsoft licences are billed separately."},
    },
    "body": lambda: "".join([
        hero("Microsoft AI Cloud Partner",
             'Microsoft Copilot setup and training in <span class="gradient-text">Adelaide</span>',
             "Essetech sets up Microsoft Copilot, formerly Microsoft 365 Copilot, for Adelaide businesses. We check your licences, tidy up who can see which files, write your AI use policy and train your staff on their own work.",
             "Book a Free AI Readiness Briefing"),
        split("prerequisites", 'What you need before Copilot <span class="text-fire-500">works</span>',
              ["Copilot sits on top of Microsoft 365. It reads the emails, files, chats and meetings each person can already open, then answers questions and drafts work from them. So the basics have to be in place first.",
               f'Microsoft publishes the full list in its <a href="https://learn.microsoft.com/en-us/copilot/microsoft-365/microsoft-365-copilot-requirements" rel="noopener" {LINK}>Copilot requirements</a>. For a small business it comes down to the six things listed here, and we check each one before you pay for a licence.'],
              "You'll need:",
              ["An eligible Microsoft 365 plan for each person who will use Copilot.",
               "A Microsoft Copilot licence for each of those people.",
               "Work accounts in Microsoft Entra ID. We also turn on multi-factor authentication.",
               "Mailboxes in Exchange Online, so Copilot can work with email and calendars.",
               "Files stored in OneDrive and SharePoint, because Copilot can only use documents it can reach.",
               "Current versions of the Microsoft 365 apps."]),
        cards("why-setup-matters", 'Why Copilot needs a proper <span class="text-fire-500">setup</span>',
              "Copilot follows the file permissions you already have. That protects you, and it is also where the risk sits.",
              [("It shows people what they can already open", "If an old SharePoint site is shared with everyone in the company, Copilot can use it to answer anyone's question. Payroll and HR folders are the usual surprises. We find that sharing and fix it first."),
               ("Your staff are probably using AI already", "Without rules, people paste client details into free public tools. A written AI use policy tells your team what they can put into AI and what they can't."),
               ("Unused licences are wasted money", "Copilot licences often get bought and then sit idle because nobody showed staff what to use them for. Training on real tasks is what gets it used.")],
              tint=True),
        steps("how-it-runs", 'How a Copilot rollout <span class="text-fire-500">runs</span>',
              "A typical rollout takes 4 to 6 weeks and runs in this order.",
              [("Readiness check", "We review your Microsoft 365 plan, licences, sign-in security and how files are shared. You get a short written summary of what needs fixing."),
               ("Fix the sharing", "We close off overshared sites and folders and set sensible sharing defaults, so Copilot only brings up what each person should see."),
               ("Pilot group", "A small group gets Copilot first. We write your AI use policy with them and learn which tasks it helps with most."),
               ("Training", "Role-by-role sessions using your own documents and tasks. Staff leave knowing what to use Copilot for and what the rules are."),
               ("Wider rollout and review", "The rest of the team is switched on. We check how it is being used, answer questions and adjust the setup.")]),
        prices("pricing", 'Copilot setup <span class="text-fire-500">pricing</span>',
               "Starting prices for a simple setup. We confirm the final price once we've scoped the work with you. All prices exclude GST.",
               [("Copilot rollout", "Readiness check, permissions and rollout", "From $2,500", "+ GST, over 4 to 6 weeks"),
                ("AI use policy and training", "A written policy and staff sessions", "From $1,100", "+ GST"),
                ("AI readiness briefing", "Where every engagement starts", "Free", "30 minutes")],
               'Microsoft bills Copilot licences per user, separately from these prices. We include the current licence cost in your quote. See our full <a href="/pricing-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">IT and AI pricing for Adelaide</a>.',
               tint=True),
        table("copilot-or-claude", 'Copilot, Claude or <span class="text-fire-500">both?</span>',
              "We set up both. The right one depends on where your work lives.",
              ["", "Microsoft Copilot", "Claude"],
              [["Best when", "Your team works in Outlook, Teams, Word, Excel and SharePoint all day.", "You work with long documents, research, writing or analysis, or you don't run Microsoft 365."],
               ["Works with", "Your Microsoft 365 emails, files, chats and meetings.", "Files you give it, plus the apps you connect to it."],
               ["Typical first jobs", "Meeting summaries, email drafts, finding documents and first drafts of reports.", "Reviewing contracts and tenders, summarising long reports and drafting proposals."],
               ["We handle", "Licences, permissions, policy and training.", "Accounts, access rules, policy and training."]],
              'Many businesses end up using both. <a href="/secure-ai-enablement-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">Secure AI Enablement</a> is the full program.'),
    ]),
    "faq_title": 'Microsoft Copilot in Adelaide: <span class="text-fire-500">FAQs</span>',
    "faq_intro": "Common questions about setting up Microsoft Copilot in a small or medium business.",
    "faq": [
        ("How much does Microsoft Copilot setup cost in Adelaide?", "Essetech's Copilot rollout starts from $2,500 + GST, and an AI use policy with staff training starts from $1,100 + GST. We confirm the price after a free 30-minute AI readiness briefing, because it depends on your team size and how your files are shared now. Microsoft bills the Copilot licences separately, per user."),
        ("How long does a Copilot rollout take?", "A typical rollout takes 4 to 6 weeks: a readiness check, a file permissions clean-up, a pilot group, staff training and then the wider rollout."),
        ("What do we need before we can use Copilot?", "Each user needs an eligible Microsoft 365 plan, a Microsoft Copilot licence and a work account in Microsoft Entra ID. Email needs to be in Exchange Online and files in OneDrive or SharePoint. We check all of this in the readiness check."),
        ("Is our data safe with Microsoft Copilot?", "Copilot only uses content the person asking already has permission to open, and Microsoft states that prompts, responses and data accessed through Microsoft Graph aren't used to train its foundation models. The usual risk is old files shared too widely, which is why we fix sharing before switching Copilot on."),
        ("We bought Copilot licences and nobody uses them. Can you help?", "Yes. That usually means staff were never shown what to use it for. We run role-by-role training on your own documents and tasks, and set clear rules so people know what is safe."),
        ("Is Microsoft Copilot the same as Microsoft 365 Copilot?", "Yes. Microsoft has renamed Microsoft 365 Copilot to Microsoft Copilot. It is the paid, licensed version that works with your Microsoft 365 emails, files, chats and meetings."),
        ("Do you only set up Copilot in Adelaide?", WHERE),
    ],
    "cta": ("Find out if you're ready for Copilot", "Start with a free 30-minute AI readiness briefing. We'll look at your Microsoft 365 setup and tell you what needs to happen before Copilot is switched on.", "Book a Free AI Readiness Briefing"),
    "explore": pick("enablement", "ai", "m365", "cyber", "managed", "pricing"),
    "related": [("/blog/ai-for-accounting-firms.html", "AI for accounting firms: an example AI command centre"),
                ("/secure-ai-copilot-rollout-australia.html", "Secure Copilot and AI rollout across Australia"),
                ("/essential-eight-adelaide.html", "Essential Eight help in Adelaide"),
                ("/how-remote-delivery-works.html", "How we work with clients")],
})

# ---- AI consultant ---------------------------------------------------------
PAGES.append({
    "file": "ai-consultant-adelaide.html",
    "crumb": "AI Consultant Adelaide",
    "title": "AI Consultant Adelaide | Published Prices | Essetech",
    "description": "AI consultant in Adelaide for small and medium businesses. We find the work worth automating, set it up securely and train your staff. From $750 + GST.",
    "service": {
        "name": "AI Consulting Adelaide",
        "type": ["AI consulting", "AI automation", "AI readiness audit"],
        "description": "AI consulting for Adelaide small and medium businesses: an AI readiness audit, secure Microsoft Copilot or Claude rollouts, AI call answering and enquiry follow-up, an AI use policy and staff training.",
        "offer": {"minPrice": 750, "description": "Starting prices: 60-second enquiry replies from $750 + GST, AI call answering setup from $990 + GST, AI use policy and training from $1,100 + GST, Copilot or Claude rollout from $2,500 + GST."},
    },
    "body": lambda: "".join([
        hero("Based in Brooklyn Park, Adelaide",
             'AI Consultant <span class="gradient-text">Adelaide</span>',
             "Essetech is an AI consultant for Adelaide small and medium businesses. We work out where AI will save your team time or win you customers, set it up securely, and train your staff to use it.",
             "Book a Free AI Readiness Briefing"),
        cards("which-problem", 'Two different problems. Two different <span class="text-fire-500">programs.</span>',
              "Most businesses come to us with one of these. They are separate programs, and neither is a step up from the other.",
              [("You're losing time", 'Your staff spend their days in documents, email and spreadsheets, and some already paste company information into free AI tools. We roll out Microsoft Copilot or Claude properly, with access rules, a written policy and training. This is <a href="/secure-ai-enablement-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">Secure AI Enablement</a>.'),
               ("You're losing customers", 'Calls go unanswered, enquiries wait hours for a reply and old leads are never followed up. We set up AI that answers the phone, replies to new enquiries within 60 seconds and works through your old leads. This is the <a href="/ai-growth-system-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">AI Growth System</a>.')],
              cols=2),
        steps("what-we-do", 'What we do as your AI <span class="text-fire-500">consultant</span>',
              "The same five steps apply whether you have six staff or sixty.",
              [("Find the work worth automating", "We look at how your team spends its week and pick the jobs where AI will save the most time or win the most work. In the AI Action Plan you get the five jobs AI should take on first, each costed in hours and dollars."),
               ("Make it safe", "Business accounts, access rules and a written AI use policy, so client and company data stays where it should."),
               ("Build and roll out", "We set up the tools, connect them to the systems you already use and test them with a small group first."),
               ("Train your staff", "Practical sessions on real tasks, using your own documents."),
               ("Keep it running", "Our ongoing AI services are month to month with no lock-in. We keep the setup current and help staff as questions come up.")],
              tint=True),
        cards("examples", 'Where AI is <span class="text-fire-500">useful</span>',
              "A few places we see it pay off. Each link goes to more detail.",
              [("Offices on Microsoft 365", 'Meeting summaries, email drafts and finding documents with <a href="/microsoft-copilot-consultant-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">Microsoft Copilot</a>, once file permissions are tidied up.'),
               ("Accounting firms", 'An AI command centre that reads email, Xero, Teams and the calendar overnight and sends one ranked briefing. See <a href="/blog/ai-for-accounting-firms.html" class="font-semibold text-fire-500 hover:text-fire-600">our example build</a>.'),
               ("Trades and construction", 'AI help with quotes, follow-ups and the office inbox. See <a href="/it-for-trades-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">IT and AI for trades</a>.'),
               ("Medical clinics", '<a href="/it-for-medical-clinics-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">IT and AI help</a> for GP, specialist and allied health clinics.'),
               ("Not-for-profits", '<a href="/it-for-not-for-profits-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">IT and AI help</a> for organisations working across several sites.'),
               ("Any business with a phone", 'AI call answering and 60-second replies to new enquiries with the <a href="/ai-growth-system-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">AI Growth System</a>.')]),
        split("questions-to-ask", 'Questions to ask any AI <span class="text-fire-500">consultant</span>',
              ["AI consultants range from one-person prompt coaches to software firms. These questions sort them quickly, and you should ask us the same ones.",
               "Essetech is an IT and cybersecurity business first. That matters because most AI problems in a small business turn out to be access and data problems."],
              "Ask them:",
              ["Where does our data go, and is it used to train the AI?",
               "Who owns the accounts and the automations if we stop working with you?",
               "Can you show us one working, not a slide deck?",
               "What will it cost to run each month after setup?",
               "Who trains our staff, and on what?",
               "What happens to our security settings and file permissions?"],
              tint=True),
        table("pricing", 'AI consulting <span class="text-fire-500">prices</span>',
              "Starting prices are for a simple setup. We confirm the final price once we've scoped the work with you. All prices exclude GST.",
              ["Work", "Starting price"],
              [["AI readiness briefing, 30 minutes", "Free"],
               ["The AI Action Plan (an AI readiness audit)", "Fixed fee, credited to your rollout if you go ahead within 60 days"],
               ["Microsoft Copilot or Claude rollout", "From $2,500 + GST"],
               ["AI use policy and staff training", "From $1,100 + GST"],
               ["AI call answering setup", "From $990 + GST"],
               ["60-second replies to new enquiries", "From $750 + GST"],
               ["Lead reactivation campaign", "From $1,500 + GST"],
               ["Monthly running cost after setup (AI Growth System)", "From $199 a month + GST"]],
              'These match our full <a href="/pricing-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">IT and AI pricing for Adelaide</a>.'),
    ]),
    "faq_title": 'AI Consultant Adelaide: <span class="text-fire-500">FAQs</span>',
    "faq_intro": "Common questions about hiring an AI consultant for a small or medium business.",
    "faq": [
        ("What does an AI consultant do?", "An AI consultant works out which parts of your business AI can usefully take over, sets up the tools and trains your staff. At Essetech that means finding the jobs worth automating, making sure data and access are secure, rolling the tools out and keeping them running."),
        ("How much does an AI consultant cost in Adelaide?", "Essetech publishes starting prices. A Microsoft Copilot or Claude rollout starts from $2,500 + GST, an AI use policy with staff training from $1,100 + GST, AI call answering setup from $990 + GST and 60-second enquiry replies from $750 + GST. Every engagement starts with a free 30-minute AI readiness briefing, and we confirm a price before any work starts."),
        ("Which AI tools do you work with?", "Mostly Microsoft Copilot, Anthropic's Claude and Google Gemini, chosen to fit the systems you already run. Where a job needs it, we build custom AI agents and automations on top."),
        ("Is it safe to put business data into AI?", "It depends on the tool and how it is set up. Free public tools are the risk. We set up business-grade AI inside your own secured environment, with access controls and a written AI use policy, so staff know what can and can't go into it."),
        ("How quickly will we see something working?", "A Copilot or Claude rollout typically runs 4 to 6 weeks. The AI Growth System is typically live within 2 to 4 weeks of your audit."),
        ("Do you work with small businesses?", "Yes. We work with businesses from a handful of staff through to a few hundred, and scale the work to your size and systems."),
        ("Do you only work in Adelaide?", WHERE),
    ],
    "cta": ("Find out where AI would help", "Start with a free 30-minute AI readiness briefing. Tell us how your team spends its week and we'll tell you where AI is worth it and where it isn't.", "Book a Free AI Readiness Briefing"),
    "explore": pick("enablement", "growth", "copilot", "consulting", "cyber", "pricing"),
    "related": [("/blog/ai-for-accounting-firms.html", "AI for accounting firms: an example AI command centre"),
                ("/ai-automation-consultant-australia.html", "AI automation consultant across Australia"),
                ("/secure-ai-copilot-rollout-australia.html", "Secure Copilot and AI rollout across Australia"),
                ("/how-remote-delivery-works.html", "How we work with clients")],
})

# ---- Essential Eight -------------------------------------------------------
PAGES.append({
    "file": "essential-eight-adelaide.html",
    "crumb": "Essential Eight Adelaide",
    "title": "Essential Eight Adelaide | Small Business Help | Essetech",
    "description": "Essential Eight help for Adelaide small businesses: a free security audit, a plain-English plan and the eight controls put in place. From $139 a user.",
    "service": {
        "name": "Essential Eight Implementation Adelaide",
        "type": ["Cybersecurity", "Essential Eight implementation"],
        "description": "Essential Eight help for Adelaide small and medium businesses: a free security audit against the eight controls, a plain-English plan, and the controls put in place and kept in place.",
        "offer": {"minPrice": 139, "unit": "per user per month", "description": "Essential Eight controls and Microsoft 365 security are included in the Support + Security managed IT plan at $139 per user per month + GST and in Fully Managed at $175. Security on its own is quoted per user per month."},
    },
    "body": lambda: "".join([
        hero("ACSC Essential Eight",
             'Essential Eight help in <span class="gradient-text">Adelaide</span>',
             "The Essential Eight is the Australian Signals Directorate's list of eight security controls that stop most common cyber attacks. Essetech checks where your Adelaide business stands against them and puts them in place, one control at a time.",
             "Book a Free Security Audit"),
        cards("the-eight", 'The eight controls in plain <span class="text-fire-500">English</span>',
              f'These are the eight strategies as listed by the Australian Signals Directorate in <a href="https://www.cyber.gov.au/publication/essential-eight-explained" rel="noopener" {LINK}>Essential Eight explained</a>.',
              [("1. Patch applications", "Keep programs such as web browsers, Microsoft Office and PDF readers up to date, so known holes are closed quickly."),
               ("2. Patch operating systems", "Keep Windows and macOS updated, and replace versions the maker no longer supports."),
               ("3. Multi-factor authentication", "A second step when signing in, such as a code or an app prompt, so a stolen password is not enough on its own."),
               ("4. Restrict administrative privileges", "Only the people who need admin rights have them, and they don't use those accounts for email or web browsing."),
               ("5. Application control", "Only approved programs can run, which stops most malicious software from starting."),
               ("6. Restrict Microsoft Office macros", "Block macros that come from the internet and allow only the ones your business needs."),
               ("7. User application hardening", "Turn off risky features in browsers and Office that attackers rely on, such as web ads and old plug-ins."),
               ("8. Regular backups", "Back up important data, keep copies where an attacker can't reach them and test that you can restore.")],
              cols=4),
        table("maturity-levels", 'The maturity levels <span class="text-fire-500">explained</span>',
              "Each control is measured at one of four levels. You pick a target level, then bring all eight controls up to it.",
              ["Level", "What it means"],
              [["Maturity Level Zero", "There are gaps in your basic defences."],
               ["Maturity Level One", "You are protected against common attacks that use widely available tools and are aimed at anyone."],
               ["Maturity Level Two", "You are protected against attackers willing to put more time and effort into targeting you."],
               ["Maturity Level Three", "You are protected against skilled attackers who adapt their methods to a specific target."]],
              f'The Australian Signals Directorate says that, generally, Maturity Level One may be suitable for small to medium enterprises. See its <a href="https://www.cyber.gov.au/publication/essential-eight-maturity-model-faq" rel="noopener" {LINK}>Essential Eight maturity model FAQ</a>.',
              tint=True),
        steps("how-we-do-it", 'How we get a small business <span class="text-fire-500">there</span>',
              "We work through it one control at a time, so nothing stops your team working.",
              [("A free security audit", "We check each of the eight controls on your computers, Microsoft 365 and backups."),
               ("A plain-English plan", "You get a written list of what is in place and what is missing, in priority order, with costs."),
               ("The controls go in", "We start with the gaps that carry the most risk. For most small businesses that means multi-factor authentication, patching and backups."),
               ("They stay in", "On a managed IT plan we keep patching, monitoring and backup tests running, and report to you each month.")]),
        split("who-asks", 'Who asks about the Essential <span class="text-fire-500">Eight</span>',
              ["The Essential Eight is not a legal requirement for most private businesses. It is the benchmark Australian organisations get measured against, so the question tends to arrive from outside.",
               "When it does, a written record of where you stand on each control is the quickest way to answer it."],
              "You'll usually hear about it from:",
              ["A cyber insurer, on the application or renewal form.",
               "A government or enterprise customer, in a tender or supplier questionnaire.",
               "An auditor or your board, after a breach somewhere in your industry.",
               "Your own staff, after a phishing email gets through."],
              tint=True),
        prices("pricing", 'What it <span class="text-fire-500">costs</span>',
               "Essential Eight controls are part of our managed IT plans. All prices exclude GST.",
               [("Support + Security", "Microsoft 365 security and Essential Eight controls", "$139", "per user per month + GST"),
                ("Fully Managed", "Adds cloud management", "$175", "per user per month + GST"),
                ("Security audit", "Where every engagement starts", "Free", "with a written plan")],
               'Keeping your current IT provider? We quote security on its own, per user per month. See our full <a href="/pricing-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">IT and AI pricing for Adelaide</a>.'),
    ]),
    "faq_title": 'Essential Eight Adelaide: <span class="text-fire-500">FAQs</span>',
    "faq_intro": "Common questions about the Essential Eight for small and medium businesses.",
    "faq": [
        ("What is the Essential Eight?", "The Essential Eight is a set of eight security controls published by the Australian Signals Directorate through its Australian Cyber Security Centre. They are: patch applications, patch operating systems, multi-factor authentication, restrict administrative privileges, application control, restrict Microsoft Office macros, user application hardening and regular backups."),
        ("Is the Essential Eight mandatory for small businesses?", "No, not for most private businesses. It is a mandatory baseline for many Australian Government bodies. For private businesses it is the recognised benchmark, and cyber insurers, government customers and larger clients often ask how you measure up against it."),
        ("What maturity level should a small business aim for?", "The Australian Signals Directorate says that, generally, Maturity Level One may be suitable for small to medium enterprises. We agree a target with you after the security audit, based on what you hold and who you work for."),
        ("How much does Essential Eight help cost in Adelaide?", "At Essetech, Essential Eight controls and Microsoft 365 security are included in the Support + Security managed IT plan at $139 per user per month + GST, and in Fully Managed at $175. If you want security without managed IT, we quote it per user per month. The first step, a security audit, is free."),
        ("How long does it take to put the Essential Eight in place?", "It depends on where you start. A business already on Microsoft 365 with modern computers can have the first controls, such as multi-factor authentication and patching, in place quickly. Application control and macro rules take longer because they need testing against the software you use. The plan we give you sets out the order and the timing."),
        ("Do we have to replace our IT provider?", "No. We can put the controls in alongside your current provider, or include them in a managed IT plan."),
        ("Is antivirus enough?", "No. Antivirus is one layer. The Essential Eight also covers software updates, sign-in security, admin rights, macros and backups."),
    ],
    "cta": ("Find out where you stand", "Book a free security audit. We'll check your business against the eight controls and give you a plain-English plan, yours to keep whether or not you hire us.", "Book a Free Security Audit"),
    "explore": pick("cyber", "managed", "m365", "consulting", "copilot", "pricing"),
    "related": [("/cybersecurity-adelaide.html", "Cybersecurity services in Adelaide"),
                ("/case-studies/deidentified-network-remediation/", "Network remediation case study"),
                ("/blog/it-support-cost-adelaide-2027.html", "IT support costs in Adelaide"),
                ("/how-remote-delivery-works.html", "How we work with clients")],
})

# ---- Microsoft 365 support -------------------------------------------------
PAGES.append({
    "file": "microsoft-365-support-adelaide.html",
    "crumb": "Microsoft 365 Support Adelaide",
    "title": "Microsoft 365 Support Adelaide | Setup & Help | Essetech",
    "description": "Microsoft 365 support in Adelaide: Outlook, Teams, SharePoint and OneDrive set up, secured and fixed. $150 an hour, or from $99 a user a month.",
    "service": {
        "name": "Microsoft 365 Support Adelaide",
        "type": ["Microsoft 365 support", "Microsoft 365 migration", "IT support"],
        "description": "Microsoft 365 support for Adelaide small businesses: Outlook and Exchange Online, Teams, SharePoint, OneDrive, sign-in security and licences. Available by the hour or on a monthly managed IT plan.",
        "offer": {"minPrice": 99, "unit": "per user per month", "description": "Pay as you go at $150 an hour + GST, or managed IT from $99 per user per month + GST. Microsoft 365 security is in the $139 plan and cloud management in the $175 plan."},
    },
    "body": lambda: "".join([
        hero("Microsoft AI Cloud Partner",
             'Microsoft 365 support in <span class="gradient-text">Adelaide</span>',
             "Essetech sets up, secures and fixes Microsoft 365 for Adelaide small businesses: email, Teams, SharePoint, OneDrive and sign-in security. Pay by the hour or put it on a monthly plan.",
             "Book a Free IT Audit"),
        cards("what-we-fix", 'What we look <span class="text-fire-500">after</span>',
              "The Microsoft 365 jobs Adelaide businesses call us about most.",
              [("Email and Outlook", "Mailboxes that won't sync, shared mailboxes, calendars, email on phones, and spam or phishing getting through."),
               ("Teams", "Meetings, calling, channels and guest access, set up so people can find things."),
               ("SharePoint and OneDrive", "File structure, permissions and sync problems. We also move files off old servers and USB drives."),
               ("Sign-in and security", "Multi-factor authentication, password resets, blocked sign-ins and access rules."),
               ("New starters and leavers", "Accounts created, licences assigned and access removed on the right day."),
               ("Licences", "The right plan for each person, and no paying for people who have left.")]),
        split("security-settings", 'Security settings small businesses often <span class="text-fire-500">miss</span>',
              ["Microsoft 365 is secure when it is configured properly. Several settings that matter are left for you to turn on, and most small businesses we see have missed a few.",
               'These line up with the <a href="/essential-eight-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">Essential Eight</a>, the security benchmark Australian businesses get measured against.'],
              "We check and set:",
              ["Multi-factor authentication on every account, including admins.",
               "Separate admin accounts that aren't used for everyday email.",
               "Old sign-in methods that skip multi-factor authentication, switched off.",
               "Limits on sharing files outside the business from SharePoint and OneDrive.",
               "Email protection against phishing and spoofing, including SPF, DKIM and DMARC.",
               "Backups of your Microsoft 365 data, tested by restoring from them."],
              tint=True),
        steps("migration", 'Moving to Microsoft <span class="text-fire-500">365</span>',
              "For businesses still on an old server, another email host or a mix of personal accounts.",
              [("A free cloud assessment", "We look at what you run now, how much data there is and which plan fits."),
               ("A fixed-fee quote", "Simple Microsoft 365 migrations are quoted as a fixed fee before work starts."),
               ("The move", "We test first and run the old and new systems side by side during the switch, so your team can keep working."),
               ("Handover", "Your staff are shown where everything is, and we stay on for the questions that follow.")]),
        prices("pricing", 'Microsoft 365 support <span class="text-fire-500">pricing</span>',
               "Pay for the time you use, or put Microsoft 365 on a monthly plan. All prices exclude GST.",
               [("Pay as you go", "Remote or onsite, billed for time spent", "$150", "per hour + GST in business hours"),
                ("Support + Security", "Help desk plus Microsoft 365 security", "$139", "per user per month + GST"),
                ("Fully Managed", "Adds Microsoft 365 management", "$175", "per user per month + GST")],
               'The Support plan without the security layer is $99 per user per month + GST. Remote help has a $75 minimum. See our full <a href="/pricing-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">IT and AI pricing for Adelaide</a>.',
               tint=True),
        split("copilot-ready", 'Thinking about <span class="text-fire-500">Copilot?</span>',
              ["Microsoft Copilot works from the emails and files each person can already open. If sharing in SharePoint and OneDrive is messy, Copilot will surface things people shouldn't see.",
               'Getting Microsoft 365 tidy is the first step. Our <a href="/microsoft-copilot-consultant-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">Microsoft Copilot setup</a> page covers the licences, the clean-up and the training.'],
              "Before Copilot, we check:",
              ["Who can open each SharePoint site and shared folder.",
               "That files live in OneDrive and SharePoint, not on desktops.",
               "That every account has multi-factor authentication.",
               "That each person has a plan Copilot can be added to."]),
    ]),
    "faq_title": 'Microsoft 365 Support Adelaide: <span class="text-fire-500">FAQs</span>',
    "faq_intro": "Common questions about Microsoft 365 support for small businesses.",
    "faq": [
        ("How much does Microsoft 365 support cost in Adelaide?", "Essetech charges $150 an hour + GST in business hours for pay-as-you-go support, with a $75 minimum for remote help. On a monthly plan, managed IT is $99 per user per month + GST for Support, $139 for Support + Security, which includes Microsoft 365 security, and $175 for Fully Managed, which adds cloud management."),
        ("Can you fix a Microsoft 365 problem today?", "Call 0404 311 791. We aim to respond within 30 minutes, Monday to Friday, 8am to 6pm, and most everyday Microsoft 365 problems can be fixed with a remote session."),
        ("Can you move us to Microsoft 365 from another email system?", "Yes. Simple Microsoft 365 migrations are quoted as a fixed fee. We test first and run the old and new systems side by side during the switch, so your team can keep working."),
        ("Which Microsoft 365 plan should a small business choose?", "Most small businesses choose Microsoft 365 Business Standard or Business Premium. Business Premium adds device management and stronger security features, so it suits businesses that hold client data. We check what you already pay for before recommending a change."),
        ("Do you support Google Workspace as well?", "Yes. We support Microsoft 365, Azure, AWS and Google Workspace."),
        ("Do we need a contract?", "No. Pay-as-you-go support has no contract, and our managed IT plans have no lock-in."),
        ("Do you only work in Adelaide?", WHERE),
    ],
    "cta": ("Get Microsoft 365 working properly", "Book a free IT audit. We'll look at your Microsoft 365 setup, tell you what needs fixing and what it costs.", "Book a Free IT Audit"),
    "explore": pick("support", "managed", "cloud", "e8", "copilot", "pricing"),
    "related": [("/cloud-solutions-adelaide.html", "Cloud solutions and migrations in Adelaide"),
                ("/blog/it-support-cost-adelaide-2027.html", "IT support costs in Adelaide"),
                ("/remote-it-support-australia.html", "Remote IT support across Australia"),
                ("/how-remote-delivery-works.html", "How we work with clients")],
})

# ---- IT consulting ---------------------------------------------------------
PAGES.append({
    "file": "it-consulting-adelaide.html",
    "crumb": "IT Consulting Adelaide",
    "title": "IT Consulting Adelaide | Small Business IT Advice | Essetech",
    "description": "IT consulting in Adelaide for small and medium businesses: IT reviews, Microsoft 365 and cloud planning, security and vendor advice. $150 an hour + GST.",
    "service": {
        "name": "IT Consulting Adelaide",
        "type": ["IT consulting", "IT review", "IT strategy"],
        "description": "IT consulting for Adelaide small and medium businesses: IT reviews, Microsoft 365 and cloud planning, security reviews against the Essential Eight, IT provider and vendor reviews, and project advice.",
        "offer": {"minPrice": 150, "unit": "per hour", "description": "IT consulting at $150 an hour + GST in business hours. Ongoing IT leadership as a fractional IT manager is $2,200 a month + GST for 2 days or $4,400 for 4 days."},
    },
    "body": lambda: "".join([
        hero("Founder-led IT advice",
             'IT Consulting <span class="gradient-text">Adelaide</span>',
             "Essetech is an IT consulting business in Brooklyn Park, Adelaide. We review what you have, tell you in plain English what to fix and what to leave alone, and can do the work or manage whoever does.",
             "Book a Free IT Audit"),
        cards("what-we-advise-on", 'What we\'re asked to advise <span class="text-fire-500">on</span>',
              "Most consulting work starts with one of these questions.",
              [("An IT review", "A check of your computers, network, Microsoft 365, backups and security, with a ranked list of what to fix."),
               ("Microsoft 365 and cloud planning", "Whether to move off the server, which plan to buy and how to migrate without stopping work."),
               ("A security review", 'Where you stand against the <a href="/essential-eight-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">Essential Eight</a>, and what a client, insurer or auditor is likely to ask.'),
               ("An IT provider or vendor review", "Whether you are getting what you pay for, and whether a quote in front of you is reasonable."),
               ("Projects", "Office moves, new sites, network upgrades and system changes, planned and run to a budget."),
               ("AI readiness", 'Where AI would save time, and what needs fixing first so it is safe. See <a href="/ai-consultant-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">AI consulting</a>.')]),
        steps("how-it-works", 'How it <span class="text-fire-500">works</span>',
              "The first two steps cost you nothing.",
              [("We have a look", "We spend a free hour on what you run, what keeps breaking and what your team complains about most."),
               ("You get it in writing", "A short plain-English summary of what is putting you at risk, what to fix first and what it costs. It is yours to keep whether or not you hire us."),
               ("We do the work, or manage it", "We can fix what we found, or manage your current IT provider while they do."),
               ("We report", "You get a note on what was done, so there is a record.")],
              tint=True),
        table("hourly-or-fractional", 'Hourly advice or a fractional IT <span class="text-fire-500">manager?</span>',
              "Two ways to buy IT advice from us. Which one fits depends on whether you have a question or a gap.",
              ["", "Hourly consulting", "Fractional IT manager"],
              [["Best for", "A one-off question, review or project.", "A business with 10 to 80 staff that needs someone to own IT."],
               ["Price", "$150 an hour + GST in business hours.", "$2,200 a month + GST for 2 days, or $4,400 for 4 days."],
               ["Commitment", "None. You pay for the time spent.", "A set number of days each month, reviewed after three months."],
               ["You get", "Advice and a written summary.", "Planning, vendor management, security oversight and a plain-English report."]],
              'More detail on the <a href="/fractional-it-manager-adelaide.html" class="font-semibold text-fire-500 hover:text-fire-600">fractional IT manager</a> page.'),
        split("who-you-deal-with", 'Who you deal <span class="text-fire-500">with</span>',
              ["Jonathon Battifuoco founded Essetech and works hands-on with every client. You deal with him directly, not a help desk queue.",
               'There is more about how we work, and an example of the output, in our <a href="/case-studies/deidentified-network-remediation/" class="font-semibold text-fire-500 hover:text-fire-600">de-identified network remediation case study</a>.'],
              "What you can expect:",
              ["Published prices, in Australian dollars, excluding GST.",
               "No lock-in contracts for IT support or managed IT.",
               "A reply to new enquiries within one business day.",
               "On-site work across the Adelaide metro area, from Brooklyn Park.",
               "Plain English, in person and in writing."],
              tint=True),
    ]),
    "faq_title": 'IT Consulting Adelaide: <span class="text-fire-500">FAQs</span>',
    "faq_intro": "Common questions about IT consulting for small and medium businesses.",
    "faq": [
        ("What does an IT consultant do for a small business?", "An IT consultant reviews your computers, network, cloud systems and security, tells you what to fix and in what order, and helps you plan and budget. Essetech also does the work, or manages your existing IT provider while they do it."),
        ("How much does IT consulting cost in Adelaide?", "Essetech charges $150 an hour + GST in business hours for consulting and IT support. For ongoing IT leadership, a fractional IT manager is $2,200 a month + GST for 2 days or $4,400 for 4 days, with extra days at $1,200 + GST. The first conversation is free."),
        ("Do we have to switch IT providers?", "No. Many businesses keep their existing provider for day-to-day support. We can advise alongside them or manage them on your behalf."),
        ("Can you review our current IT provider's work or a quote we've been given?", "Yes. We check what you are paying for against what you are getting, and tell you whether a quote is reasonable."),
        ("Will we get a written report?", "Yes. After the first look you get a short plain-English summary of what is putting you at risk, what to fix first and what it costs. It is yours to keep whether or not you hire us."),
        ("Which parts of Adelaide do you cover?", "We work across the Adelaide metro area from our base in Brooklyn Park, SA 5032, and remotely with businesses anywhere in Australia."),
    ],
    "cta": ("Talk to us about your IT", "Tell us where you're based, how many people work in your business and what's giving you trouble. The first conversation is free.", "Book a Free IT Audit"),
    "explore": pick("fractional", "support", "managed", "e8", "ai", "pricing"),
    "related": [("/blog/fractional-it-manager-vs-msp.html", "Fractional IT manager or MSP"),
                ("/blog/it-support-cost-adelaide-2027.html", "IT support costs in Adelaide"),
                ("/case-studies/deidentified-network-remediation/", "Network remediation case study"),
                ("/how-remote-delivery-works.html", "How we work with clients")],
})


# ------------------------------------------------------------------- build

def attr(text):
    return html.escape(text, quote=True)


def head(page):
    url = f"{BASE}/{page['file']}"
    service = page["service"]
    offer = service["offer"]
    spec = {"@type": "UnitPriceSpecification", "priceCurrency": "AUD", "minPrice": offer["minPrice"],
            "valueAddedTaxIncluded": False, "description": offer["description"]}
    if offer.get("unit"):
        spec["unitText"] = offer["unit"]
    blocks = [
        {"@context": "https://schema.org", "@type": ["LocalBusiness", "ProfessionalService"], "@id": BASE + "/#business", "name": "Essetech"},
        {"@context": "https://schema.org", "@type": "Service", "name": service["name"], "url": url,
         "provider": {"@type": "LocalBusiness", "@id": BASE + "/#business", "name": "Essetech", "url": BASE + "/"},
         "areaServed": [{"@type": "City", "name": "Adelaide"}, {"@type": "Country", "name": "Australia"}],
         "description": service["description"], "serviceType": service["type"],
         "offers": {"@type": "Offer", "priceCurrency": "AUD", "availability": "https://schema.org/InStock", "priceSpecification": spec}},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in page["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": page["crumb"], "item": url}]},
    ]
    ld = "\n".join('    <script type="application/ld+json">%s</script>' % json.dumps(b, ensure_ascii=False, separators=(",", ":")) for b in blocks)
    title, desc = attr(page["title"]), attr(page["description"])
    return f'''<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <meta name="robots" content="index, follow">
    <meta name="author" content="Essetech">
    <meta name="geo.region" content="AU-SA">
    <meta name="geo.placename" content="Adelaide">
    <link rel="canonical" href="{url}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{BASE}/og-image.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:locale" content="en_AU">
    <meta property="og:site_name" content="Essetech">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{BASE}/og-image.png">

{ld}

'''


def main():
    shell = open(SHELL, encoding="utf-8").read()
    styles = shell[shell.index('    <link rel="stylesheet" href="/tailwind.css">'):shell.index("<main")]
    tail = shell[shell.index("    </main>"):]
    for page in PAGES:
        if len(page["title"]) > 60 or len(page["description"]) > 158:
            print("  !! title/description too long on", page["file"], len(page["title"]), len(page["description"]))
        body = page["body"]()
        cta_h2, cta_text, cta_button = page["cta"]
        out = (head(page) + styles + '<main id="main">\n' + body
               + faq(page["faq_title"], page["faq_intro"], page["faq"])
               + cta(cta_h2, cta_text, cta_button)
               + explore(page["explore"]) + related(page["related"]) + "\n" + tail)
        open(page["file"], "w", encoding="utf-8").write(out)
        words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", body)))
        print("built %-46s title %d, description %d, about %d words in the body" % (page["file"], len(page["title"]), len(page["description"]), words))


if __name__ == "__main__":
    sys.exit(main())
