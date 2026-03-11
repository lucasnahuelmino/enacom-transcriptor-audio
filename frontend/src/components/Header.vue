<template>
  <div class="enacom-header">
    <!-- Background decorativo -->
    <div class="absolute inset-0 bg-gradient-radial opacity-10 pointer-events-none"></div>
    
    <div class="relative z-10 flex items-center justify-between w-full">
      <!-- Izquierda: Icono + Título -->
      <div class="flex items-center gap-4">
        <div class="text-4xl filter drop-shadow-lg">🎧</div>
        <div>
          <h1 class="text-2xl font-extrabold text-white tracking-tight leading-tight">
            Transcriptor de audios a texto
          </h1>
          <p class="text-sm text-white/65 mt-1 font-medium tracking-wide">
            Dirección Nacional de Control y Fiscalización
          </p>
        </div>
      </div>
      
      <!-- Derecha: Badge de versión + Logo -->
      <div class="flex flex-col items-end gap-2.5">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold text-white/75 uppercase tracking-wider bg-white/12 border border-white/20 rounded-full">
          <span class="w-1.5 h-1.5 bg-green-400 rounded-full shadow-glow-green"></span>
          v3.0
        </span>
        
        <!-- Logo ENACOM -->
        <div class="h-14 flex items-center">
          <span class="text-xl font-black text-white/88 tracking-widest">ENACOM</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// No hay lógica en este componente, es puramente presentacional
</script>

<style scoped>
.enacom-header {
  @apply relative;
  @apply flex items-center justify-between;
  @apply px-7 py-5;
  @apply bg-gradient-to-br from-enacom-blue-dark via-[#003d8f] to-enacom-blue-main;
  @apply rounded-enacom;
  @apply mb-6;
  @apply overflow-hidden;
  box-shadow: 0 4px 20px rgba(0, 80, 179, 0.22);
}

.enacom-header::before {
  content: '';
  @apply absolute inset-0;
  background-image:
    radial-gradient(circle at 80% 50%, rgba(255, 255, 255, 0.06) 0%, transparent 55%),
    repeating-linear-gradient(-45deg, transparent, transparent 24px, rgba(255, 255, 255, 0.025) 24px, rgba(255, 255, 255, 0.025) 25px);
  pointer-events: none;
}

.shadow-glow-green {
  box-shadow: 0 0 6px #4ade80;
}
</style>
