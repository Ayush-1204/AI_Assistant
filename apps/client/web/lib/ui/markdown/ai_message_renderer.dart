import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as md;
import 'package:url_launcher/url_launcher_string.dart';
import 'builders/code_block_builder.dart';
import 'builders/inline_code_builder.dart';
import 'builders/math_builder.dart';
import 'builders/table_builder.dart';
import 'builders/callout_builder.dart';
import 'parsers/latex_syntax.dart';

class AiMessageRenderer extends StatelessWidget {
  final String text;
  final bool isAssistant;
  final bool isStreaming;
  final Widget Function(Uri, String?, String?)? imageBuilder;
  final Map<String, MarkdownElementBuilder>? builders;
  final Iterable<md.InlineSyntax>? inlineSyntaxes;
  final Iterable<md.BlockSyntax>? blockSyntaxes;
  final bool wrapInSelectionArea;

  const AiMessageRenderer({
    Key? key,
    required this.text,
    this.isAssistant = false,
    this.isStreaming = false,
    this.imageBuilder,
    this.builders,
    this.inlineSyntaxes,
    this.blockSyntaxes,
    this.wrapInSelectionArea = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    Widget body = MarkdownBody(
      data: text,
      selectable: false, // Turned off to use SelectionArea instead
      extensionSet: md.ExtensionSet.gitHubFlavored,
      styleSheet: MarkdownStyleSheet(
        pPadding: const EdgeInsets.only(bottom: 16),
        listBulletPadding: const EdgeInsets.only(right: 8),
        p: TextStyle(
          fontSize: 15,
          height: 1.6,
          color: Colors.white.withValues(alpha: 0.9),
        ),
        h1: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, height: 1.5, color: Colors.white),
        h1Padding: const EdgeInsets.only(top: 32, bottom: 16),
        h2: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, height: 1.4, color: Colors.white),
        h2Padding: const EdgeInsets.only(top: 24, bottom: 12),
        h3: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600, height: 1.4, color: Colors.white),
        h3Padding: const EdgeInsets.only(top: 24, bottom: 12),
        h4: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.4, color: Colors.white),
        h4Padding: const EdgeInsets.only(top: 24, bottom: 12),
        horizontalRuleDecoration: BoxDecoration(
          border: Border(
            top: BorderSide(
              color: Colors.white.withValues(alpha: 0.1),
              width: 1,
            ),
          ),
        ),
        code: const TextStyle(
          fontSize: 14,
          fontFamily: 'monospace',
          color: Colors.orangeAccent,
          backgroundColor: Colors.transparent,
        ),
        codeblockPadding: EdgeInsets.zero,
        codeblockDecoration: const BoxDecoration(
          color: Colors.transparent,
        ),
        blockquote: TextStyle(
          fontSize: 15,
          fontStyle: FontStyle.italic,
          color: Colors.white.withValues(alpha: 0.7),
        ),
        blockquotePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        blockquoteDecoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(4),
          border: Border(
            left: BorderSide(
              color: Theme.of(context).colorScheme.primary,
              width: 4,
            ),
          ),
        ),
        a: TextStyle(
          color: Theme.of(context).colorScheme.primary,
          decoration: TextDecoration.underline,
        ),
        listIndent: 24,
      ),
      onTapLink: (text, href, title) async {
        if (href != null) {
          try {
            await launchUrlString(href, mode: LaunchMode.externalApplication);
          } catch (_) {
            try {
              await launchUrlString(href);
            } catch (_) {}
          }
        }
      },
      imageBuilder: imageBuilder,
      builders: {
        'pre': CodeBlockBuilder(context),
        'code': InlineCodeBuilder(context),
        'latex_block': MathBuilder(isDisplay: true),
        'latex_inline': MathBuilder(isDisplay: false),
        'table': TableBuilder(context),
        'callout': CalloutBuilder(),
        if (builders != null) ...builders!,
      },
      inlineSyntaxes: [
        LatexSyntax(),
        if (inlineSyntaxes != null) ...inlineSyntaxes!,
      ],
      blockSyntaxes: [
        CalloutSyntax(),
        if (blockSyntaxes != null) ...blockSyntaxes!,
      ],
    );

    Widget finalTree = Container(
      width: isAssistant ? double.infinity : null,
      color: Colors.transparent,
      child: body,
    );

    if (wrapInSelectionArea) {
      finalTree = SelectionArea(child: finalTree);
    }

    return Theme(
      data: Theme.of(context).copyWith(
        textSelectionTheme: const TextSelectionThemeData(
          selectionColor: Color(0xFF0337A1),
          selectionHandleColor: Color(0xFF0337A1),
        ),
      ),
      child: finalTree,
    );
  }
}
