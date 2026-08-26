#version 440

// Shader de refracción de "cristal líquido" para GlassPanel.qml.
//
// Idea: el panel es transparente en el centro (se ve el fondo sin distorsión)
// y la refracción se concentra en una franja estrecha junto al borde, como si
// el cristal fuera más grueso ahí. `source` es una captura recortada del
// fondo con un margen (`padding`) alrededor del panel, para poder desplazar
// la muestra hacia contenido que está justo fuera del panel.

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 itemSize;
    float cornerRadius;
    float edgeWidth;
    float refractionStrength;
    float padding;
    vec4 tintColor;
    float topHighlightStrength;
};

layout(binding = 1) uniform sampler2D source;

// SDF de rectángulo redondeado centrado en el origen (b = semiejes, r = radio).
float roundedBoxSDF(vec2 p, vec2 b, float r) {
    vec2 q = abs(p) - b + r;
    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}

void main() {
    vec2 uv = qt_TexCoord0;
    vec2 pixel = uv * itemSize;
    vec2 halfSize = itemSize * 0.5;
    vec2 p = pixel - halfSize;

    float dist = roundedBoxSDF(p, halfSize, cornerRadius);
    if (dist > 0.0) {
        fragColor = vec4(0.0);
        return;
    }

    // 0 en el centro del panel, 1 justo en el borde interior.
    float edgeFactor = clamp(-dist / edgeWidth, 0.0, 1.0);
    edgeFactor = 1.0 - edgeFactor;
    edgeFactor = smoothstep(0.0, 1.0, edgeFactor);

    // Dirección hacia afuera del panel (gradiente numérico del SDF).
    float eps = 1.0;
    vec2 grad = vec2(
        roundedBoxSDF(p + vec2(eps, 0.0), halfSize, cornerRadius) - roundedBoxSDF(p - vec2(eps, 0.0), halfSize, cornerRadius),
        roundedBoxSDF(p + vec2(0.0, eps), halfSize, cornerRadius) - roundedBoxSDF(p - vec2(0.0, eps), halfSize, cornerRadius)
    );
    float gradLen = length(grad);
    if (gradLen > 0.0001) {
        grad /= gradLen;
    }

    // El fondo capturado (`source`) cubre el panel más `padding` alrededor.
    vec2 srcSize = itemSize + vec2(2.0 * padding);
    vec2 uvInSource = (pixel + vec2(padding)) / srcSize;
    vec2 offsetUv = grad * (edgeFactor * refractionStrength) / srcSize;
    vec2 cleanUv = clamp(uvInSource, vec2(0.001), vec2(0.999));

    // Aberración cromática sutil: cada canal se refracta con un desplazamiento
    // ligeramente distinto. Es lo que hace perceptible el cristal real incluso
    // sobre fondos muy suaves, porque introduce color nuevo en el borde en
    // vez de solo desplazar un degradado ya casi uniforme.
    vec2 uvR = clamp(uvInSource - offsetUv * 1.25, vec2(0.001), vec2(0.999));
    vec2 uvG = clamp(uvInSource - offsetUv, vec2(0.001), vec2(0.999));
    vec2 uvB = clamp(uvInSource - offsetUv * 0.75, vec2(0.001), vec2(0.999));

    vec4 refracted = vec4(
        texture(source, uvR).r,
        texture(source, uvG).g,
        texture(source, uvB).b,
        1.0
    );
    vec4 clean = texture(source, cleanUv);
    vec4 baseColor = mix(clean, refracted, edgeFactor);

    // Tinte mínimo: nunca queda blanco puro, ni en el centro más limpio.
    baseColor.rgb = mix(baseColor.rgb, tintColor.rgb, tintColor.a);

    // Filo claro en el borde superior: más intenso cuanto más arriba y más
    // cerca del borde exterior del panel.
    float topness = clamp(-p.y / halfSize.y, 0.0, 1.0);
    float rim = edgeFactor * topness * topness * topHighlightStrength;
    baseColor.rgb += vec3(rim);

    fragColor = vec4(baseColor.rgb, 1.0) * qt_Opacity;
}
