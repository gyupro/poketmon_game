shader_type canvas_item;
// 그레이스케일(4단계) 이미지를 슈퍼게임보이 4색 팔레트로 치환

uniform vec4 c0 : source_color = vec4(1.0);
uniform vec4 c1 : source_color = vec4(0.66, 0.66, 0.66, 1.0);
uniform vec4 c2 : source_color = vec4(0.33, 0.33, 0.33, 1.0);
uniform vec4 c3 : source_color = vec4(0.0, 0.0, 0.0, 1.0);

void fragment() {
	vec4 t = texture(TEXTURE, UV);
	float v = t.r;
	vec3 col = v > 0.83 ? c0.rgb : (v > 0.5 ? c1.rgb : (v > 0.17 ? c2.rgb : c3.rgb));
	COLOR = vec4(col, t.a * COLOR.a);
}
