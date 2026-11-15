---
name: top-issue-pr
description: Wählt aus den offenen GitHub-Issues eines Repos das wichtigste aus, lässt es von einem Sonnet-Subagenten umsetzen, der einen Pull Request stellt, und reviewt diesen PR anschließend selbst. Verwende diesen Skill, wenn der Nutzer sagt „Entscheid dich für das wichtigste Issue und setz es um“, „nimm das wichtigste Issue und mach einen PR“, „arbeite das dringendste Issue ab“, „pick the most important issue and fix it in a PR“ oder Ähnliches – auch wenn Subagent, Sonnet oder Review nicht ausdrücklich erwähnt werden, solange es darum geht, selbst ein Issue zu priorisieren und per PR umzusetzen.
---

# Wichtigstes Issue umsetzen: Subagent baut, du reviewst

Ablauf: Du priorisierst und bereitest vor, ein Sonnet-Subagent setzt um und stellt den PR, du reviewst unabhängig. Die Aufteilung hat einen Grund. Die Priorisierung und das Review brauchen Urteilsvermögen und den Kontext, den du hast. Die Umsetzung ist meist gut abgegrenzte Arbeit, die ein günstigeres Modell zuverlässig erledigt, solange der Auftrag vollständig ist. Das Review ist nur etwas wert, wenn du es nicht vom Bericht des Subagenten abschreibst.

## 1. Offene Issues einlesen

- GitHub-Tools per ToolSearch laden, z. B. `select:mcp__github__list_issues,mcp__github__issue_read`, und offene Issues abrufen. Wenn die Tools fehlen, `gh` verwenden, sofern es verfügbar und erlaubt ist.
- Gibt es keine offenen Issues, das sagen und aufhören. Erfinde keine eigenen.
- Hat der Nutzer ein bestimmtes Issue genannt, nimm dieses und überspring Schritt 2.

## 2. Das wichtigste Issue wählen

Wäge ab, statt nach Label oder Nummer zu gehen:

- **Wirkung**: Wie viele Nutzer oder Besucher trifft es, und wie stark? Kaputte oder extrem langsame Funktionen wiegen schwerer als Kosmetik.
- **Risiko**: Sicherheit, Datenverlust, rechtliche Risiken.
- **Eignung für einen PR**: Lässt es sich in einem abgegrenzten, prüfbaren PR lösen?

Zurückstellen, auch wenn sie wichtig sind:

- Aufgaben, die eine menschliche Entscheidung oder Fachverantwortung brauchen, etwa Rechtstexte wie eine Datenschutzerklärung.
- Aufgaben, die nur mit Force-Push oder History-Rewrite auf geteilten Branches gehen.
- Aufgaben, für die nötige Zugänge fehlen.

Nenne in zwei, drei Sätzen deine Wahl und warum. Erwähne kurz den stärksten Kandidaten, den du nicht genommen hast, und warum. Dann weiter, ohne auf eine Bestätigung zu warten. Der Nutzer hat die Entscheidung bewusst dir überlassen.

## 3. Vorbereiten, bevor du delegierst

Der Subagent startet ohne deinen Kontext. Alles, was er wissen muss, gehört in seinen Auftrag.

- Issue-Text vollständig lesen und die betroffenen Dateien selbst ansehen, damit du konkrete Pfade, Funktionen und Zusammenhänge nennen kannst.
- **Branch klären**: Nimm den Branch, den die Git-Anweisungen der Session vorgeben. Hat dieser Branch schon einen offenen, nicht gemergten PR, landen neue Commits in diesem PR und vermischen zwei Themen. Frag den Nutzer in diesem Fall, ob du stapeln, einen anderen Branch nehmen oder warten sollst.
- Default-Branch (Base) ermitteln und nachsehen, ob es ein PR-Template gibt.
- Die Attributionszeilen für Commits und PR-Text aus dem System-Reminder der Session übernehmen.

## 4. Subagent starten

Agent-Tool mit `subagent_type: "general-purpose"`, `model: "sonnet"` und `run_in_background: false`, weil dein nächster Schritt vom Ergebnis abhängt. Schreib den Auftrag in der Sprache des Nutzers und mit diesen Teilen:

1. **Kontext**: Repo-Pfad, ausgecheckter Branch, kurze Beschreibung des Projekts und der relevanten Dateien.
2. **Problem**: Issue-Nummer und der Kern des Issues mit konkreten Zahlen und Fundstellen.
3. **Aufgabe**: nummerierte Schritte mit genug Detail, um die Lösung festzulegen, zum Beispiel welche Funktion wie geändert wird. Ein Hilfsskript, das nur einmal läuft, gehört ins Scratchpad, nicht ins Repo.
4. **Scope-Grenzen**: Nur dieses Issue. Andere Issues nicht mitfixen, auch wenn sie im Weg liegen, sondern sie im PR-Text erwähnen. Kein Force-Push, kein History-Rewrite, keine fachfremden Änderungen.
5. **Verifikation vor dem Commit**: konkrete Prüfungen, die zum Issue passen, etwa Tests, Syntaxchecks, Zählungen oder ein Vorher/Nachher-Vergleich. Wo Netz oder Dienste fehlen: offline testen, was geht, und Ungetestetes ausdrücklich melden.
6. **Commit, Push, PR**:
   - Commit-Message mit den Attributionszeilen.
   - `git push -u origin <branch>`, bei Netzwerkfehlern mit Retries.
   - PR über `mcp__github__create_pull_request`, vorher per ToolSearch laden. Überschriften des PR-Templates übernehmen, falls vorhanden.
   - PR-Text: was geändert wurde, wie es verifiziert ist, was offen bleibt, mögliche Folgeschritte und `Closes #N`, am Ende die PR-Attributionszeilen.
   - Keine Modellbezeichnungen außer den vorgegebenen Attributionszeilen.
7. **Rückmeldung**: PR-URL und Nummer, Commit-Hashes, geänderte Dateien, Verifikationsergebnisse, und was nicht geklappt hat oder ungetestet ist.

## 5. PR selbst reviewen

Der Bericht des Subagenten sagt dir, wo du hinschauen solltest. Er ist kein Beweis.

- Den Diff selbst lesen, z. B. mit `git show --stat`, `git show <commit> -- <datei>` oder `git diff <base>...HEAD`. Bei vielen Binärdateien die Stat-Ausgabe filtern.
- Die wichtigsten Behauptungen nachprüfen: Zahlen nachrechnen und Verifikationen stichprobenartig selbst ausführen. Bei visuellen Ergebnissen wie Bildern oder Seiten etwas tatsächlich ansehen.
- Scope prüfen: Wurde nur das Issue gelöst? Sind Hilfsskripte oder Debug-Reste versehentlich im Commit?
- Folgen über den Diff hinaus bedenken: neue Abhängigkeiten, Deploy- und Build-Schritte, Migrationen, Dinge, die auf dem Server nachgezogen werden müssen.

Du kannst den PR weder approven noch mergen, das macht der Nutzer.

## 6. Ergebnis an den Nutzer

Kurz und in der Sprache des Nutzers:

- PR-Link, welches Issue er schließt, und in einem Satz, warum dieses Issue.
- **Fazit**: mergebereit oder nicht.
- **Vor dem Merge oder Deploy zu tun**: echte Blocker und nötige Handgriffe, zuerst.
- **Ungetestet**: was nicht live geprüft werden konnte, und deine Einschätzung des Risikos.
- **Gut zu wissen**: Folgeschritte und kleine Anmerkungen.

Das Review steht zunächst nur im Chat. Biete am Ende an, es als PR-Kommentar zu posten und den PR auf CI und Kommentare zu beobachten. Mach beides erst, wenn der Nutzer zustimmt.
