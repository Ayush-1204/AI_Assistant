import 'package:markdown/markdown.dart' as md;

class LatexSyntax extends md.InlineSyntax {
  LatexSyntax()
      : super(r'(?<!\\)(?:\$\$(.*?)\$\$|\$(?!\s)(.*?)(?<!\s)\$|\\\[(.*?)\\\]|\\\((.*?)\\\))');

  @override
  bool onMatch(md.InlineParser parser, Match match) {
    // Determine the type of match based on which group matched
    final String content;
    final bool isDisplay;

    if (match[1] != null) {
      // $$...$$
      content = match[1]!;
      isDisplay = true;
    } else if (match[2] != null) {
      // $...$
      content = match[2]!;
      isDisplay = false;
    } else if (match[3] != null) {
      // \[...\]
      content = match[3]!;
      isDisplay = true;
    } else if (match[4] != null) {
      // \(...\)
      content = match[4]!;
      isDisplay = false;
    } else {
      return false;
    }

    final el = md.Element.text(isDisplay ? 'latex_block' : 'latex_inline', content);
    parser.addNode(el);
    return true;
  }
}
