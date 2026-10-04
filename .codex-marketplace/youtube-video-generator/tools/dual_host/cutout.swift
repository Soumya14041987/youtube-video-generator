// Cut the main person out of a photo using Apple's on-device Vision framework (macOS 14+).
// Usage: swiftc -O cutout.swift -o cutout && ./cutout input.jpg output.png
import Foundation
import Vision
import CoreImage
import CoreImage.CIFilterBuiltins

let args = CommandLine.arguments
guard args.count == 3 else { print("usage: cutout input output.png"); exit(1) }
guard let input = CIImage(contentsOf: URL(fileURLWithPath: args[1])) else { print("cannot read input"); exit(1) }

let handler = VNImageRequestHandler(ciImage: input)
let request = VNGenerateForegroundInstanceMaskRequest()
do { try handler.perform([request]) } catch { print("vision failed: \(error)"); exit(2) }
guard let result = request.results?.first else { print("no subject found"); exit(3) }

do {
    let maskBuffer = try result.generateScaledMaskForImage(forInstances: result.allInstances, from: handler)
    let mask = CIImage(cvPixelBuffer: maskBuffer)
    let blend = CIFilter.blendWithMask()
    blend.inputImage = input
    blend.backgroundImage = CIImage(color: .clear).cropped(to: input.extent)
    blend.maskImage = mask
    guard let output = blend.outputImage else { print("blend failed"); exit(4) }
    let context = CIContext()
    try context.writePNGRepresentation(of: output, to: URL(fileURLWithPath: args[2]), format: .RGBA8,
                                       colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
    print("cutout written")
} catch {
    print("mask failed: \(error)"); exit(5)
}
