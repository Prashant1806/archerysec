# -*- coding: utf-8 -*-
#                    _
#     /\            | |
#    /  \   _ __ ___| |__   ___ _ __ _   _
#   / /\ \ | '__/ __| '_ \ / _ \ '__| | | |
#  / ____ \| | | (__| | | |  __/ |  | |_| |
# /_/    \_\_|  \___|_| |_|\___|_|   \__, |
#                                     __/ |
#                                    |___/
# Copyright (C) 2017 Anand Tiwari
#
# Email:   anandtiwarics@gmail.com
# Twitter: @anandtiwarics
#
# This file is part of ArcherySec Project.

import hashlib
import uuid
from datetime import datetime

from dashboard.views import trend_update
from staticscanners.models import StaticScanResultsDb, StaticScansDb
from utility.email_notify import email_sch_notify

Details = "NA"
classname = "NA"
ShortMessage = "NA"
sourcepath = "NA"
sourcefile = "NA"
LongMessage = "NA"
name = ""
vul_col = ""
lenth_match = ""
duplicate_hash = ""
vul_id = ""
total_vul = ""
total_high = ""
total_medium = ""
total_low = ""


def xml_parser(root, project_id, scan_id):
    """

    :param root:
    :param project_id:
    :param scan_id:
    :return:
    """
    date_time = datetime.now()
    global name, classname, risk, ShortMessage, LongMessage, sourcepath, vul_col, ShortDescription, Details, lenth_match, duplicate_hash, vul_id, total_vul, total_high, total_medium, total_low
    # print root
    for bug in root:
        if bug.tag == "BugInstance":
            name = bug.attrib["type"]
            priority = bug.attrib["priority"]
            for BugInstance in bug:
                if BugInstance.tag == "ShortMessage":
                    global ShortMessage
                    ShortMessage = BugInstance.text
                if BugInstance.tag == "LongMessage":
                    global LongMessage
                    LongMessage = BugInstance.text
                if BugInstance.tag == "Class":
                    global classname
                    classname = BugInstance.attrib["classname"]
                if BugInstance.tag == "SourceLine":
                    global sourcepath, sourcefile
                    sourcepath = BugInstance.attrib["sourcepath"]
                    sourcefile = BugInstance.attrib["sourcefile"]

                if priority == "1":
                    risk = "High"
                    vul_col = "danger"

                elif priority == "2":
                    risk = "Medium"
                    vul_col = "warning"

                elif priority == "3":
                    risk = "Low"
                    vul_col = "info"

                vul_id = uuid.uuid4()

                dup_data = name + classname + risk

                duplicate_hash = hashlib.sha256(dup_data.encode("utf-8")).hexdigest()

                match_dup = StaticScanResultsDb.objects.filter(
                    dup_hash=duplicate_hash
                ).values("dup_hash")
                lenth_match = len(match_dup)

            if lenth_match == 0:
                duplicate_vuln = "No"

                false_p = StaticScanResultsDb.objects.filter(
                    false_positive_hash=duplicate_hash
                )
                fp_lenth_match = len(false_p)

                if fp_lenth_match == 1:
                    false_positive = "Yes"
                else:
                    false_positive = "No"

                save_all = StaticScanResultsDb(
                    vuln_id=vul_id,
                    date_time=date_time,
                    scan_id=scan_id,
                    project_id=project_id,
                    title=name,
                    severity=risk,
                    description=str(ShortMessage)
                    + "\n\n"
                    + str(LongMessage)
                    + "\n\n"
                    + str(classname),
                    fileName=sourcepath,
                    severity_color=vul_col,
                    vuln_status="Open",
                    dup_hash=duplicate_hash,
                    vuln_duplicate=duplicate_vuln,
                    false_positive=false_positive,
                    scanner="Findbugs",
                )
                save_all.save()

            else:
                duplicate_vuln = "Yes"

                save_all = StaticScanResultsDb(
                    vuln_id=vul_id,
                    date_time=date_time,
                    scan_id=scan_id,
                    project_id=project_id,
                    title=name,
                    severity=risk,
                    description=str(ShortMessage)
                    + "\n\n"
                    + str(LongMessage)
                    + "\n\n"
                    + str(classname),
                    fileName=sourcepath,
                    severity_color=vul_col,
                    vuln_status="Duplicate",
                    dup_hash=duplicate_hash,
                    vuln_duplicate=duplicate_vuln,
                    false_positive="Duplicate",
                    scanner="Findbugs",
                )
                save_all.save()

        if bug.tag == "BugPattern":
            for BugPattern in bug:
                name = bug.attrib["type"]
                if BugPattern.tag == "ShortDescription":
                    ShortDescription = BugPattern.text
                if BugPattern.tag == "Details":
                    global Details
                    Details = BugPattern.text

                StaticScanResultsDb.objects.filter(scan_id=scan_id, title=name).update(
                    description=str(Details)
                    + "\n\n"
                    + str(ShortMessage)
                    + "\n\n"
                    + str(LongMessage)
                    + "\n\n"
                    + str(classname),
                )

        all_findbugs_data = StaticScanResultsDb.objects.filter(
            scan_id=scan_id, false_positive="No"
        )

        duplicate_count = StaticScanResultsDb.objects.filter(
            scan_id=scan_id, vuln_duplicate="Yes"
        )

        total_vul = len(all_findbugs_data)
        total_high = len(all_findbugs_data.filter(severity="High"))
        total_medium = len(all_findbugs_data.filter(severity="Medium"))
        total_low = len(all_findbugs_data.filter(severity="Low"))
        total_duplicate = len(duplicate_count.filter(vuln_duplicate="Yes"))

        StaticScansDb.objects.filter(scan_id=scan_id).update(
            total_vul=total_vul,
            date_time=date_time,
            high_vul=total_high,
            medium_vul=total_medium,
            low_vul=total_low,
            total_dup=total_duplicate,
            scanner="Findbugs",
        )
    trend_update()
    subject = "Archery Tool Scan Status - Findbugs Report Uploaded"
    message = (
        "Findbugs Scanner has completed the scan "
        "  %s <br> Total: %s <br>High: %s <br>"
        "Medium: %s <br>Low %s"
        % (scan_id, total_vul, total_high, total_medium, total_low)
    )

    email_sch_notify(subject=subject, message=message)
