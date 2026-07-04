// Local OCR via Apple's Vision framework.
// Usage: swift scripts/ocr_vision.swift <image-path>
// Prints recognized text (one line per detected text line), reading order
// top-to-bottom then left-to-right, honoring the image's EXIF orientation.
//
// Purpose: digitize photos of books the user physically owns without routing
// the text through the model. Output should be redirected to a file.
import Foundation
import Vision
import ImageIO
import CoreGraphics

let args = CommandLine.arguments
guard args.count > 1 else {
    FileHandle.standardError.write("usage: ocr_vision <image-path>\n".data(using: .utf8)!)
    exit(2)
}
let url = URL(fileURLWithPath: args[1])
guard let src = CGImageSourceCreateWithURL(url as CFURL, nil),
      let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
    FileHandle.standardError.write("error: could not load image\n".data(using: .utf8)!)
    exit(1)
}
let props = CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as? [CFString: Any]
let orientRaw = (props?[kCGImagePropertyOrientation] as? UInt32) ?? 1
let orientation = CGImagePropertyOrientation(rawValue: orientRaw) ?? .up

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cg, orientation: orientation, options: [:])
do {
    try handler.perform([request])
} catch {
    FileHandle.standardError.write("error: \(error)\n".data(using: .utf8)!)
    exit(1)
}
guard let obs = request.results else { exit(0) }
// Vision uses a bottom-left origin (y increases upward). Sort column-first so a
// two-page spread reads left page fully, then right page — bucket by whether the
// line STARTS left or right of center. Single-page poems land entirely in the
// left bucket, so ordering is unchanged for them. Within a column: top-to-bottom,
// then left-to-right.
func col(_ o: VNRecognizedTextObservation) -> Int { o.boundingBox.origin.x < 0.5 ? 0 : 1 }
let sorted = obs.sorted { a, b in
    let ca = col(a), cb = col(b)
    if ca != cb { return ca < cb }
    let ay = a.boundingBox.origin.y, by = b.boundingBox.origin.y
    if abs(ay - by) > 0.012 { return ay > by }
    return a.boundingBox.origin.x < b.boundingBox.origin.x
}
for o in sorted {
    if let t = o.topCandidates(1).first { print(t.string) }
}
