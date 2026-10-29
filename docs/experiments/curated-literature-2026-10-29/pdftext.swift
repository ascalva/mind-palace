// Extract a PDF's text with Apple's PDFKit (no third-party tool): pdftext <in.pdf> <out.txt>
import Foundation
import PDFKit

let args = CommandLine.arguments
guard args.count == 3, let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
    FileHandle.standardError.write("usage: pdftext <in.pdf> <out.txt>\n".data(using: .utf8)!)
    exit(2)
}
var pages: [String] = []
for i in 0..<doc.pageCount {
    if let text = doc.page(at: i)?.string { pages.append(text) }
}
let text = pages.joined(separator: "\n\n")
try text.write(toFile: args[2], atomically: true, encoding: .utf8)
print("\(doc.pageCount) pages, \(text.count) chars")
