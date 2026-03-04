import numpy as np

class UserCalibration:
    def __init__(self):
        # Listas de coeficientes: [c0, c1, c2...] para a equação c0 + c1*x + c2*x^2
        self.temp_coeffs = []
        self.rad_coeffs = []

    def set_temp_coeffs(self, coeffs):
        self.temp_coeffs = coeffs

    def set_rad_coeffs(self, coeffs):
        self.rad_coeffs = coeffs

    def has_temp_cal(self):
        return len(self.temp_coeffs) > 0

    def has_rad_cal(self):
        return len(self.rad_coeffs) > 0

    def apply(self, raw_counts, coeffs):
        """
        Aplica o polinômio à matriz raw_counts.
        A fórmula assumida é: y = c0 + c1*x + c2*x^2 + ...
        """
        if not coeffs:
            return raw_counts
            
        # O np.polyval espera a ordem [cn, cn-1, ..., c0] (do maior grau para o menor).
        # Como o usuário geralmente insere [c0, c1, c2], nós invertemos a lista:
        rev_coeffs = coeffs[::-1]
        
        # Converte a matriz inteira de uma vez e garante que seja float para evitar overflow
        return np.polyval(rev_coeffs, raw_counts.astype(float))