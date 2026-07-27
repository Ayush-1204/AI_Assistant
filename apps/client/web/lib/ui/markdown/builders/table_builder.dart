import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as md;

class TableBuilder extends MarkdownElementBuilder {
  final BuildContext context;

  TableBuilder(this.context);

  @override
  Widget? visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    // element.children contains thead and tbody
    if (element.children == null || element.children!.isEmpty) return null;

    final rows = <TableRow>[];
    
    // Parse thead and tbody
    for (var child in element.children!) {
      if (child is md.Element) {
        if (child.tag == 'thead') {
          rows.addAll(_parseRows(child, true, preferredStyle));
        } else if (child.tag == 'tbody') {
          rows.addAll(_parseRows(child, false, preferredStyle));
        }
      }
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E1E),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          )
        ]
      ),
      clipBehavior: Clip.antiAlias,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Table(
          defaultColumnWidth: const IntrinsicColumnWidth(),
          border: TableBorder(
            horizontalInside: BorderSide(color: Colors.white.withValues(alpha: 0.05), width: 1),
            verticalInside: BorderSide(color: Colors.white.withValues(alpha: 0.05), width: 1),
          ),
          children: rows,
        ),
      ),
    );
  }

  List<TableRow> _parseRows(md.Element parent, bool isHeader, TextStyle? preferredStyle) {
    final rows = <TableRow>[];
    if (parent.children == null) return rows;

    for (var i = 0; i < parent.children!.length; i++) {
      var tr = parent.children![i];
      if (tr is md.Element && tr.tag == 'tr') {
        final cells = <Widget>[];
        if (tr.children != null) {
          for (var td in tr.children!) {
            if (td is md.Element) {
              cells.add(
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  color: isHeader 
                      ? Colors.white.withValues(alpha: 0.05) 
                      : (i % 2 == 1 ? Colors.white.withValues(alpha: 0.02) : Colors.transparent),
                  alignment: Alignment.centerLeft,
                  child: Text(
                    td.textContent,
                    style: TextStyle(
                      fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
                      fontSize: 15,
                      color: Colors.white.withValues(alpha: isHeader ? 1.0 : 0.8),
                    ),
                  ),
                )
              );
            }
          }
        }
        rows.add(TableRow(children: cells));
      }
    }
    return rows;
  }
}
