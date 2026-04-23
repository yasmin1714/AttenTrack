class AttentionScorer:

    def calculate(self,
                  face_detected,
                  eyes_closed,
                  sleeping,
                  looking_away,
                  phone_detected):

        current_penalty = 0

        if not face_detected:
            current_penalty += 50
        else:
            if sleeping:
                current_penalty += 60
            elif eyes_closed:
                current_penalty += 30

            if looking_away:
                current_penalty += 35

            if phone_detected:
                current_penalty += 50

        score = max(0, 100 - current_penalty)

        # Status logic
        if score > 80:
            status = "ATTENTIVE"
            color = (0, 255, 0)
        elif score > 50:
            status = "DISTRACTED"
            color = (0, 165, 255)
        else:
            status = "NOT PAYING ATTENTION"
            color = (0, 0, 255)

        return score, status, color