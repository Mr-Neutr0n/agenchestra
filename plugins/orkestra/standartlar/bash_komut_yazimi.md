# Bash komutu yazımı (ADR-0151)

Ajanın Bash aracına verdiği komut içindir; kullanıcıya verilen terminal komutu için `kabuk_profili.md` geçerlidir.

## Kural

- Kısa komut satır içinde kalır: tek iş, az tırnak, iç içe tırnak yok.
- Uzun ya da tırnak yoğun betik (20 satırı aşan `python -c`, `bash -c` ya da heredoc; iç içe `'` ve `"`; ters eğik çizgi ile kaçırılmış ters tırnak) satır içine yazılmaz.
- Yerine iki adım:
  1. Betiği **Write** aracıyla dosyaya yaz (scratchpad ya da işin çalışma klasörü).
  2. Bash ile yalnız dosyayı çalıştır: `python <dosya>.py` ya da `bash <dosya>.sh`.
- Heredoc ile dosya üretme (`cat > x <<'EOF'`) yerine Write kullan; dosya içeriği kabuk ayrıştırmasından geçmez.
- Büyük komut (tek tırnaklar kaçışla büyüdüğünde yaklaşık 7700 karakter) aracın komut satırı sınırında kesilir ve `unexpected EOF` verir; bu boyuttaki her şey dosyaya gider.

## Neden

- Kabuk tırnakları ayrıştırır, betik dili de ayrıca ayrıştırır; iki katman bir arada kaçış hatası üretir.
- Hata komut koşunca görünür ve tur kaybettirir; dosyadaki betik Write'tan sonra olduğu gibi çalışır.

## Ret gelirse

`bash -n` ret verdiyse ya da komut uzunluk sınırını aştıysa aynı komutu düzeltip yeniden satır içine yazma: betiği Write ile dosyaya yaz, sonra çalıştır.
