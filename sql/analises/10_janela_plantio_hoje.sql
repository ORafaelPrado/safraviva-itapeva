-- Pergunta: o que posso plantar hoje em Itapeva e com qual risco (ZARC vigente)?
-- Técnicas: CTE com a safra mais recente que cobre cada cultura, filtro por data, string_agg ordenado.
WITH vigente AS (
    SELECT nome_cultura, max(safra) AS safra
    FROM analytics.janela_plantio
    WHERE codigo_ibge = 3522406
    GROUP BY nome_cultura
)
SELECT
    j.nome_cultura,
    j.manejo,
    j.ciclo,
    string_agg(j.solo || ' (' || j.nivel_risco || ', até ' || strftime(j.data_fim, '%d/%m') || ')', '; '
               ORDER BY j.cod_solo)                      AS solos_indicados_hoje
FROM analytics.janela_plantio j
JOIN vigente v USING (nome_cultura, safra)
WHERE j.codigo_ibge = 3522406
  AND current_date BETWEEN j.data_inicio AND j.data_fim
  AND regexp_matches(j.nome_cultura, '^(Soja|Milho|Feijão|Trigo|Sorgo Granífero|Aveia|Cevada)')  -- culturas do sistema regional
GROUP BY ALL
ORDER BY j.nome_cultura, j.manejo, j.ciclo;
