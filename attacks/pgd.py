def PGD(input, target, model, clip_min, clip_max, optimizer=None, device="cpu"):
    input_variable = input.detach().clone()
    input_variable.requires_grad = True
    model.zero_grad()
    result = model(input_variable)
    if args.zoom_factor != 8:
        h = int((target.size()[1] - 1) / 8 * args.zoom_factor + 1)
        w = int((target.size()[2] - 1) / 8 * args.zoom_factor + 1)
        # 'nearest' mode doesn't support align_corners mode and 'bilinear' mode is fine for downsampling
        target = F.interpolate(target.unsqueeze(1).float(), size=(h, w), mode='bilinear', align_corners=True).squeeze(1).long()

    ignore_label = 255
    criterion = nn.CrossEntropyLoss(ignore_index=ignore_label).to(device)
    loss = criterion(result, target.detach())
    loss.backward()
    
    print("Loss:", loss.item())

    ################################################################################
    adversarial_example = input.detach().clone()
    adversarial_example[:, 0, :, :] = adversarial_example[:, 0, :, :] * std_origin[0] + mean_origin[0]
    adversarial_example[:, 1, :, :] = adversarial_example[:, 1, :, :] * std_origin[1] + mean_origin[1]
    adversarial_example[:, 2, :, :] = adversarial_example[:, 2, :, :] * std_origin[2] + mean_origin[2]
    adversarial_example = optimizer.step(-1*input_variable.grad, adversarial_example)
    adversarial_example = torch.max(adversarial_example, clip_min)
    adversarial_example = torch.min(adversarial_example, clip_max)
    adversarial_example = torch.clamp(adversarial_example, min=0.0, max=1.0)

    adversarial_example[:, 0, :, :] = (adversarial_example[:, 0, :, :] - mean_origin[0]) / std_origin[0]
    adversarial_example[:, 1, :, :] = (adversarial_example[:, 1, :, :] - mean_origin[1]) / std_origin[1]
    adversarial_example[:, 2, :, :] = (adversarial_example[:, 2, :, :] - mean_origin[2]) / std_origin[2]
    ################################################################################
    return adversarial_example



def BIM(input, target, model, eps=0.03, k_number=2, alpha=0.01, device="cpu"):
    optimizer = Adam_optimizer(lr=alpha, B1=0.9, B2=0.99)
    
    input_unnorm = input.clone().detach()
    input_unnorm[:, 0, :, :] = input_unnorm[:, 0, :, :] * std_origin[0] + mean_origin[0]
    input_unnorm[:, 1, :, :] = input_unnorm[:, 1, :, :] * std_origin[1] + mean_origin[1]
    input_unnorm[:, 2, :, :] = input_unnorm[:, 2, :, :] * std_origin[2] + mean_origin[2]
    clip_min = input_unnorm - eps
    clip_max = input_unnorm + eps

    adversarial_example = input.detach().clone()
    adversarial_example.requires_grad = True
    
    for mm in range(k_number):
        adversarial_example = PGD(adversarial_example, target, model, clip_min, clip_max, optimizer, device)
        adversarial_example = adversarial_example.detach()
        adversarial_example.requires_grad = True
        model.zero_grad()
    return adversarial_example